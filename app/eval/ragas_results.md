# RAGAS-style eval — 2026-08-27

Scored **15** answerable questions (refusal rows excluded; the guard eval covers those). LLM judge: `gpt-4o-mini`, temperature 0.

| metric | mean |
|---|:---:|
| faithfulness (grounding) | **1.00** |
| answer relevance | **0.76** |
| context precision | **0.92** |

| # | question | faithful | relevance | ctx precision |
|---|----------|:--------:|:---------:|:-------------:|
| 1 | How many days of unemployment am I allowed on post-completion OPT? | 1.00 | 0.89 | 1.00 |
| 2 | Can I start working before my EAD start date? | 1.00 | 0.84 | 1.00 |
| 3 | When can I apply for post-completion OPT? | 1.00 | 0.78 | 1.00 |
| 4 | Does part-time work count toward maintaining OPT status? | 1.00 | 0.87 | 0.50 |
| 5 | How long is the grace period after my OPT ends? | 1.00 | 0.77 | 1.00 |
| 6 | How long is the STEM OPT extension, and who's eligible? | 1.00 | 0.84 | 1.00 |
| 7 | Do I need a job offer to apply for OPT? | 1.00 | 0.75 | 1.00 |
| 8 | How soon must I report a change of employer? | 1.00 | 0.66 | 1.00 |
| 9 | Can I travel internationally while on OPT? | 1.00 | 0.78 | 0.83 |
| 10 | What is cap-gap? | 1.00 | 0.58 | 1.00 |
| 11 | Can I do volunteer or unpaid work to avoid unemployment days? | 1.00 | 0.59 | 0.83 |
| 12 | Is self-employment allowed on OPT? | 1.00 | 0.74 | 1.00 |
| 13 | What happens if my program ends while my OPT application is still pending? | 1.00 | 0.74 | 0.70 |
| 14 | Can I work for more than one employer on OPT? | 1.00 | 0.81 | 1.00 |
| 15 | Does my OPT job have to relate to my major? | 1.00 | 0.79 | 1.00 |

---

### Q1. How many days of unemployment am I allowed on post-completion OPT?

- **faithfulness** 1.00 (2/2 claims supported)
- **answer relevance** 0.89 — generated Qs: ['How long can I be unemployed during my post-completion OPT period?', 'What is the maximum number of days I can be unemployed while on post-completion OPT?', 'Is there a limit to the amount of unemployment I can have during my post-completion OPT?']
- **context precision** 1.00 — chunk verdicts: [True, True, True, False, False]

### Q2. Can I start working before my EAD start date?

- **faithfulness** 1.00 (1/1 claims supported)
- **answer relevance** 0.84 — generated Qs: ['Can I start working before the start date on my Employment Authorization Document (EAD)?', 'Is it permissible to begin employment prior to the official start date listed on my EAD?', 'What are the rules regarding starting work with an Employment Authorization Document (EAD)?']
- **context precision** 1.00 — chunk verdicts: [True, True, True, False, False]

### Q3. When can I apply for post-completion OPT?

- **faithfulness** 1.00 (3/3 claims supported)
- **answer relevance** 0.78 — generated Qs: ['What are the eligibility requirements for applying for post-completion Optional Practical Training (OPT)?', 'When is the earliest and latest I can apply for post-completion OPT?', 'What is the timeframe for filing an application after my Designated School Official recommends OPT in SEVIS?']
- **context precision** 1.00 — chunk verdicts: [True, True, False, False, False]

### Q4. Does part-time work count toward maintaining OPT status?

- **faithfulness** 1.00 (2/2 claims supported)
- **answer relevance** 0.87 — generated Qs: ['Does part-time work count towards maintaining OPT status?', 'What are the work hour requirements for maintaining post-completion OPT status?', 'Can I work part-time while on post-completion OPT and still maintain my status?']
- **context precision** 0.50 — chunk verdicts: [False, True, False, False, False]

### Q5. How long is the grace period after my OPT ends?

- **faithfulness** 1.00 (5/5 claims supported)
- **answer relevance** 0.77 — generated Qs: ['What is the grace period for an F-1 student after their OPT EAD expires?', 'What options does an F-1 student have during the 60-day grace period after completing OPT?', 'Can an F-1 student change their education level or transfer schools during the grace period after OPT?']
- **context precision** 1.00 — chunk verdicts: [True, True, False, False, False]

### Q6. How long is the STEM OPT extension, and who's eligible?

- **faithfulness** 1.00 (6/6 claims supported)
- **answer relevance** 0.84 — generated Qs: ['What are the eligibility requirements for the STEM OPT extension?', 'How long is the STEM OPT extension period?', 'What must an F-1 student do to qualify for the STEM OPT extension after completing their degree?']
- **context precision** 1.00 — chunk verdicts: [True, True, True, False, False]

### Q7. Do I need a job offer to apply for OPT?

- **faithfulness** 1.00 (3/3 claims supported)
- **answer relevance** 0.75 — generated Qs: ['Is a job offer necessary to apply for Optional Practical Training (OPT)?', 'What are the eligibility requirements for applying for OPT?', 'What are the employment expectations for students authorized for post-completion OPT?']
- **context precision** 1.00 — chunk verdicts: [True, True, False, False, False]

### Q8. How soon must I report a change of employer?

- **faithfulness** 1.00 (1/1 claims supported)
- **answer relevance** 0.66 — generated Qs: ['What is the timeframe for reporting a change of employer to my DSO?', 'How soon should I inform my DSO if I change my employer?', 'What is the requirement for notifying my DSO about a new job?']
- **context precision** 1.00 — chunk verdicts: [True, True, True, False, False]

### Q9. Can I travel internationally while on OPT?

- **faithfulness** 1.00 (6/6 claims supported)
- **answer relevance** 0.78 — generated Qs: ['Can I travel internationally while on Optional Practical Training (OPT)?', 'What documents do I need to re-enter the United States while on OPT?', 'Does traveling outside the United States affect my OPT period or unemployment time?']
- **context precision** 0.83 — chunk verdicts: [True, False, True, False, False]

### Q10. What is cap-gap?

- **faithfulness** 1.00 (7/7 claims supported)
- **answer relevance** 0.58 — generated Qs: ['What is cap-gap in relation to F-1 students and H-1B petitions?', 'What conditions must be met for an F-1 student to qualify for cap-gap extension?', 'When does the cap-gap period begin and end for F-1 students transitioning to H-1B status?']
- **context precision** 1.00 — chunk verdicts: [True, True, True, True, False]

### Q11. Can I do volunteer or unpaid work to avoid unemployment days?

- **faithfulness** 1.00 (5/5 claims supported)
- **answer relevance** 0.59 — generated Qs: ['Can I do volunteer work to avoid unemployment days while studying?', 'What are the requirements for volunteering while on a student visa?', 'Do I need to report my volunteer work to my school or immigration authorities?']
- **context precision** 0.83 — chunk verdicts: [True, False, True, False, False]

### Q12. Is self-employment allowed on OPT?

- **faithfulness** 1.00 (4/4 claims supported)
- **answer relevance** 0.74 — generated Qs: ['Can a student on post-completion OPT be self-employed, and what are the requirements for reporting their employment?', 'Are there any restrictions on self-employment for students on the STEM OPT extension?', 'What happens to the employer name in SEVIS if a student on post-completion OPT is self-employed?']
- **context precision** 1.00 — chunk verdicts: [True, True, False, False, False]

### Q13. What happens if my program ends while my OPT application is still pending?

- **faithfulness** 1.00 (2/2 claims supported)
- **answer relevance** 0.74 — generated Qs: ['What happens to my F-1 status if my program ends while my OPT application is pending?', 'Can I start my OPT if my program has ended but my Form I-765 is still pending?', 'What do I need to do to maintain my F-1 status while my OPT application is being processed?']
- **context precision** 0.70 — chunk verdicts: [True, False, False, False, True]

### Q14. Can I work for more than one employer on OPT?

- **faithfulness** 1.00 (4/4 claims supported)
- **answer relevance** 0.81 — generated Qs: ['Can a student on post-completion OPT work for multiple employers?', 'What is the process for a student to add an additional employer while on post-completion OPT?', 'Are there any specific steps a student must follow to manage multiple employers during their post-completion OPT period?']
- **context precision** 1.00 — chunk verdicts: [True, True, False, False, False]

### Q15. Does my OPT job have to relate to my major?

- **faithfulness** 1.00 (3/3 claims supported)
- **answer relevance** 0.79 — generated Qs: ['Does my job during Optional Practical Training (OPT) need to be related to my major?', 'What is required of me to demonstrate the connection between my OPT job and my field of study?', 'Are there any specific guidelines regarding the relevance of employment to my major during pre-completion and post-completion OPT?']
- **context precision** 1.00 — chunk verdicts: [True, True, True, True, False]
