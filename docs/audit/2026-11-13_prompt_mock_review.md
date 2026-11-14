# Request: mock peer review of a study design by four venues

This folder holds the plan of a study that has not been run yet:

- `STUDY_SUMMARY.md`: a three-page summary (start here).
- `STUDY_PROTOCOL_v2.3.md`: the full protocol (about 2,300 lines; read the sections you need).
- `REGISTRATION_v2.3.md`: the summary that will be preregistered on OSF.

No results exist. The authors are a graduate student (the principal investigator), an independent annotator who will be a co-author, and a faculty member who has been invited. The cash budget for API calls is capped at US$128, and the local models run on one 8 GB GPU. A small pilot is planned within days; the core design is preregistered before it and should not change after that.

## What to do

Write four mock reviews, one for each venue below, as an experienced reviewer of that venue would write them if the study were carried out exactly as planned and submitted there. Use each venue's own standards and reviewing style.

1. **Transactions on Machine Learning Research (TMLR)**
2. **ACL Rolling Review** (for ACL or EMNLP)
3. **Journal of Artificial Intelligence Research (JAIR)**
4. **MIS Quarterly**

For each review give:
- a summary of the study in two or three sentences;
- strengths;
- weaknesses, split into **major** and **minor**;
- questions to the authors;
- a likely recommendation (accept, minor revision, major revision, reject), with one sentence on what would change it.

Then, after the four reviews:

5. **Improvements to apply to the study.** One consolidated list, ordered by priority. For each item give:
   - what to change, and the section of the protocol it concerns;
   - which reviews raise it;
   - whether it changes the registered design (mark **[D]**) or only the framing, reporting or writing;
   - its cost in cash, in local machine time and in the authors' time, and whether it would delay the pilot.
6. **Criticisms that no improvement can answer** under this budget, and how the paper should state them.

## Rules

- Work only from the files in this folder. Do not run code.
- Be concrete and critical. Point to sections of the protocol.
- At most about 2,500 words in total. Use headings and short bullet lists.
