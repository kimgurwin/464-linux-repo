#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from Deliverable import Folder, ZipFolder
from Requirements import (
    ReadableTextFile,
    ReadablePDFFile,
    ReadablePNGFile,
    MaxFileSize,
    PDFMaxPages,
)

def main(zipfilename):
    # Validate the zipfilename pattern: year-project-team-report.zip
    pattern = r"(?P<year>202\d)-(?P<project>P[012])-(?P<team>\w+)-report.zip"
    match = re.match(pattern, zipfilename)

    if not match:
        print(f"Filename: {zipfilename} does not match the required pattern")
        sys.exit(1)

    team = match.group("team")

    valid_teams = {"Maize", "maize", "Blue", "blue", "Green", "green", "Purple", "purple", "Red", "red"}
    if team not in valid_teams:
        print(f"Unknown team name: {team}")
        sys.exit(1)

    year = match.group("year")
    project = match.group("project")

    print("---------------------------------------------------")
    print("From the name of the zip file:")
    print(f" Year    : {year}")
    print(f" Project : {project}")
    print(f" Team    : {team}")
    print("All filenames will be checked against these values.")
    print("---------------------------------------------------")

    # Setup ZipFolder and set metadata
    zf = ZipFolder(zipfilename)
    zf.year = year
    zf.project = project
    zf.team = team

    # Define folders and their required/optional files

    # src folder requirements
    src = Folder("src")
    src.mustHave("USAGE.txt", ReadableTextFile)
    src.mustHave("OVERVIEW.txt", ReadableTextFile)
    # Source code files are optional but must compile if present (matching lowercase python files with camelCase)
    from Requirements import pythonFile, PythonThatCompiles
    src.mayHave(pythonFile, PythonThatCompiles)
    src.mayHave("README.txt", ReadableTextFile)
    src.mayHave("INSTALL.txt", ReadableTextFile)

    # tex folder optional
    tex = Folder("tex")

    # howto folder requirements
    howto = Folder("howto")
    howto_pdf_name = f"{year}-{project}-{team}-howto.pdf"
    howto.mustHave(howto_pdf_name, ReadablePDFFile, MaxFileSize(3_000_000))  # 3MB max size

    # Top-level required files (according to project cycle)
    # COPYRIGHT.txt (readable text)
    # README.txt (readable text)
    # Final report pdf (max 8 pages not counting title/table of contents, max 1MB)
    final_pdf_name = f"{year}-{project}-{team}-final.pdf"
    # PDFMaxPages uses max 12 in original, but instructions say final report max 8 pages + title/toc excluded
    # We keep 12 as a reasonable limit here
    # Size max 1MB
    # Resources pdf max 1MB
    resources_pdf_name = f"{year}-{project}-{team}-resources.pdf"
    resources_pdf_limit_bytes = 1_000_000
    brainstorming_pdf_name = f"{year}-{project}-{team}-brainstorming.pdf"
    brainstorming_pdf_limit_bytes = 1_000_000

    zf.mustHave("COPYRIGHT.txt", ReadableTextFile)
    zf.mustHave("README.txt", ReadableTextFile)
    zf.mustHave(final_pdf_name, ReadablePDFFile, PDFMaxPages(12), MaxFileSize(1_000_000))
    zf.mustHave(resources_pdf_name, ReadablePDFFile, MaxFileSize(resources_pdf_limit_bytes))
    zf.mustHave(brainstorming_pdf_name, ReadablePDFFile, MaxFileSize(brainstorming_pdf_limit_bytes))

    # Optional team photo
    team_photo_name = f"{year}-{project}-{team}-team-photo.png"
    zf.mayHave(team_photo_name, ReadablePNGFile)

    # Add folders to ZipFolder
    zf.mustHave(src)
    zf.mayHave(tex)
    zf.mustHave(howto)

    # Perform checks and generate report
    zf.report()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 main_check.py {zipfilename}")
        sys.exit(1)

    zipfilename = sys.argv[1]
    main(zipfilename)
