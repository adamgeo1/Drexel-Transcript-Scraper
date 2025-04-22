from playwright.sync_api import sync_playwright
import argparse
import pandas as pd
from pathlib import Path
import fitz

# === ARGUMENT PARSING ===
parser = argparse.ArgumentParser(description="Drexel Transcript Scraper")
parser.add_argument("--course", type=str, default="MATH 221", help="Course code in the format 'DEPT NUM' (default: MATH 221)")
parser.add_argument("--login", action="store_true", help="Login for first-time setup")
parser.add_argument("--manual", action="store_true", help="Open browser in manual mode")
parser.add_argument("--firefox", action="store_true", help="Use Firefox instead of Chrome")
args = parser.parse_args()

# === CONFIGURATION ===
COURSE = args.course
BROWSER = "firefox" if args.firefox else "chrome"
CSV_PATH = "students.csv"
OUTPUT_DIR = Path.cwd() / "TranscriptDownloads"
ERROR_LOG_PATH = OUTPUT_DIR / "transcript_error_log.txt"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === Extract grades from downloaded transcript PDF ===
def getGrades(course: str, path: Path):
    courseDept, courseNum = course.split()
    grades = []  # list in case course taken multiple times
    doc = fitz.open(path)
    fullText = ""
    for page in doc:
        fullText += page.get_text() # full transcript text

    lines = fullText.split("\n") # splits by each word into list
    for line in lines:
        splitLine = line.split()
        if len(splitLine) <= 5:
            continue  # skip current or malformed lines
        if splitLine[0] == courseDept and splitLine[1] == courseNum:
            for i, elem in enumerate(splitLine):
                if ".000" in elem: # finds credits
                    if len(splitLine[i - 1]) > 2: #detects if course is current by seeing if word before credits is more than 2 characters
                        grades.append("X") # X for currently taking
                    elif splitLine[i - 1] in ["+", "-"]:
                        grades.append(splitLine[i - 2] + splitLine[i - 1])
                    else:
                        grades.append(splitLine[i - 1])
                    break
    return grades

def launchBrowser():
    if BROWSER == "firefox":
        return p.firefox.launch(headless=False)
    else:
        return p.chromium.launch(headless=False, channel="chrome")

def launchBrowserWithContext():
    browser = launchBrowser()
    return browser, browser.new_context(storage_state="storage_state.json")

def processStudent(df, idx, student_id, context, page):
    firstName = df.at[idx, "First"]
    lastName = df.at[idx, "Last"]
    try:
        href = page.locator("text=More BannerWeb Faculty Services").get_attribute("href")
        banner = context.new_page()
        print("Opening BannerWeb")
        banner.goto(href, wait_until="networkidle")
        print("Opening Advisor Menu")
        banner.click("text=Advisor Menu")
        bannerDomain = "https://banner.drexel.edu"
        link = banner.locator("text=Student Academic Transcript")
        href = link.get_attribute("href")
        print(f"✅ Found transcript link: {bannerDomain + href}")
        transcript_page = context.new_page()
        print("Opening Student Academic Transcript")
        transcript_page.goto(bannerDomain + href, wait_until="load")  # opens transcript finder in new tab
        transcript_page.select_option("select[name='term']",
                                      label="Winter Quarter 24-25")  # selects Winter 24-25 from dropdown menu
        print("Waiting for Submit button on Select Term Page")
        transcript_page.wait_for_selector('input[value="Submit"]', timeout=5000)
        print("Clicking submit")
        transcript_page.click('input[value="Submit"]')  # clicks submit, moves on to name entry page
        print("Entering last name")
        transcript_page.fill("#LN", lastName)  # enters student last name
        print("Entering first name")
        transcript_page.fill("#FN", firstName)  # enters student first name
        print("Waiting for Submit button on Student Name Page")
        transcript_page.wait_for_selector('input[value="Submit"]', timeout=5000)
        print("Clicking submit")
        transcript_page.click('input[value="Submit"]')  # clicks submit, moves onto student selection page
        print("Waiting for Submit button on Student Selection Page")
        transcript_page.wait_for_selector('input[value="Submit"]', timeout=5000)
        print("Clicking submit")
        transcript_page.click(
            'input[value="Submit"]')  # automatically clicks submit as we assume first student available is correct
        if transcript_page.locator(
                "text=ERROR").is_visible():  # if student that hasn't taken the course in quarter selected
            raise Exception(student_id)  # passes student id to error log
        print("Waiting for Display Transcript button on Student Page")
        transcript_page.wait_for_selector('input[value="Display Transcript"]', timeout=5000)
        print("Clicking display transcript")
        transcript_page.click(
            'input[value="Display Transcript"]')  # clicks display transcript to allow the page to be saved as a PDF
        print(f"Saving as StudentAcademicTranscript{student_id}.pdf in {OUTPUT_DIR}")
        transcript_page.pdf(path=OUTPUT_DIR / f"StudentAcademicTranscript{student_id}.pdf",
                            print_background=True)  # saves transcript as PDF to designated output folder
        print(f"Getting grades from PDF for {student_id}")
        grades = getGrades(COURSE,
                           OUTPUT_DIR / f"StudentAcademicTranscript{student_id}.pdf")  # calls getGrades() and passes through student transcript
        df.at[idx, COURSE] = ", ".join(
            grades) if grades else "N"  # adds student grade for given course to CSV, "N" if they haven't taken it at all
        print("Closing transcript tab")
        transcript_page.close()  # closes transcript finder tab, repeats process with next student in CSV
        print("Closing banner tab")
        banner.close()
        href, link, banner, transcript_page = None, None, None, None

    except Exception as e:
        print(f"Error for {student_id}: {e}")  # prints error on student ID
        with open(ERROR_LOG_PATH, "a") as f:
            f.write(f"{student_id}: {e}\n")  # writes student id for manual review to error_log.txt
        df.at[idx, COURSE] = "ERROR"  # puts ERROR for the course grade in CSV

def main():
    # === Main automation ===
    df = pd.read_csv(CSV_PATH)
    student_ids = df["ID"].tolist()

    if args.login:
        with sync_playwright() as p:
            browser = launchBrowser()
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://one.drexel.edu")

            # Wait for manual login
            print("⚠️ Please log in manually and complete 2FA. Then wait for window to close automatically. You have 60 seconds.")

            page.wait_for_timeout(60000)  # 60 seconds to log in manually

            # Save login cookies and local storage
            context.storage_state(path="storage_state.json")
            print("Login saved to storage_state.json")
            browser.close()

    elif args.manual:
        with sync_playwright() as p:
            browser, context = launchBrowserWithContext()
            page = context.new_page()
            page.goto("https://one.drexel.edu/", wait_until="load")  # goes straight to faculty tab
            page.wait_for_timeout(600000)
            browser.close()

    else:
        with sync_playwright() as p:
            browser, context = launchBrowserWithContext()
            page = context.new_page()
            page.goto("https://one.drexel.edu/", wait_until="load")  # goes straight to faculty tab
            page.click("text=FACULTY")
            open(ERROR_LOG_PATH, "w").close()

            for idx, student_id in enumerate(student_ids):
                processStudent(df, idx, student_id, context, page)

            df.to_csv(CSV_PATH, index=False)

if __name__ == "__main__":
    main()