# Drexel Transcript Scraper

## Requirements
- Drexel faculty login
- Python 3
- Chrome OR Firefox
- CSV file titled `students.csv` in the same directory as the `TranscriptScraper.py` file with these columns:

| Last | First | ID |
|----------|-----------|----|
| Smith    | John      | 1234 |
| Doe      | Jane      | 5678 |

- Install all requirements:
```bash
pip install -r requirements.txt
```
## Files
- `TranscriptScraper.py`: Main automation script
- `students.csv` Student data with `Last`, `First`, and `ID` columns
- `requirements.txt` Python dependencies

## Usage
⚠️ if using Firefox, all commands must also include the `--firefox` argument.\
Additionally, if no course is specified using\
`--course`, `MATH 221` will be used by default.
1. First-time login (stores session data):
`python TranscriptScraper.py --login`
This will open the browser, and you will have 60 seconds to login and authenticate using 2FA. Once logged in, it is important
that you **do not** close the browser manually, but let the browser close automatically. This creates a `stored_state.json`
file in the current working directory. You do not need to repeat this step on subsequent runs of the program, though if you
run it on another day you may need to repeat this step.
2. Now that you have your `stored_state.json`, you may run the program with your desired course number.
3. ⚠️ One common snag is that when opening a BannerWeb link, you may need to manually click `BANNER WEB` on the sign-in page
that pops up every dozen students or so.
4. Once the program finishes and the browser closes, the CSV will have all the grades for the entered course for each student.

## Arguments
- `--login`: Launches the script in a manual login mode, giving the user 60 seconds to login before automatically closing
and saving the session to `stored_state.json`
- `--course 'DEPT NUM'`: Specifies a course to search for in student transcripts, `MATH 221` if not specified.
- `--manual`: Opens Drexel One with no automation to be used for testing purposes, closes automatically in 10 minutes.
- `--firefox`: Uses Firefox instead of Chrome.


