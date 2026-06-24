# Eval baseline - 2026-06-22

- Questions: **16**
- Citation present (or correct refusal): **12/16**
- Not-legal-advice line present: **16/16**
- Refusal correct (refuses iff out-of-scope): **12/16**

> These are automatic guard checks. Eyeball factual correctness in the 'correct?' column, then record that % as your Week 1 baseline.

| # | question | cited | disclaimer | refusal ok | correct? |
|---|----------|:-----:|:----------:|:----------:|:--------:|
| 1 | How many days of unemployment am I allowed on post-completion OPT? | ✅ | ✅ | ✅ | ✅ |
| 2 | Can I start working before my EAD start date? | ✅ | ✅ | ✅ | ✅ |
| 3 | When can I apply for post-completion OPT? | ✅ | ✅ | ✅ | ✅ |
| 4 | Does part-time work count toward maintaining OPT status? | ✅ | ✅ | ✅ | ✅ |
| 5 | How long is the grace period after my OPT ends? | ✅ | ✅ | ✅ | ✅ |
| 6 | How long is the STEM OPT extension, and who's eligible? | ✅ | ✅ | ✅ | ✅ |
| 7 | Do I need a job offer to apply for OPT? | ✅ | ✅ | ✅ | ✅ |
| 8 | How soon must I report a change of employer? | ✅ | ✅ | ✅ | ✅ |
| 9 | Can I travel internationally while on OPT? | ❌ | ✅ | ❌ | ⚠️ gap |
| 10 | What is cap-gap? | ✅ | ✅ | ✅ | ✅ |
| 11 | Can I do volunteer or unpaid work to avoid unemployment days? | ❌ | ✅ | ❌ | ❌ retrieval |
| 12 | Is self-employment allowed on OPT? | ❌ | ✅ | ❌ | ⚠️ gap |
| 13 | What happens if my program ends while my OPT application is still pending? | ✅ | ✅ | ✅ | ❌ faithfulness |
| 14 | Can I work for more than one employer on OPT? | ❌ | ✅ | ❌ | ⚠️ gap |
| 15 | Does my OPT job have to relate to my major? | ✅ | ✅ | ✅ | ✅ |
| 16 | What is the capital of France? | ✅ | ✅ | ✅ | ✅ refusal |

**correct? legend:** ✅ correct · ❌ wrong, needs a fix · ⚠️ defensible refusal (genuinely not in the 7-doc federal corpus)

### Baseline: 11/16 (~69%) behaving correctly
10 correct answers + 1 correct out-of-scope refusal (Q16). Citation discipline 11/11 on answered; disclaimer 16/16.

### Failure analysis — Week 2 targets
- **Q11 — retrieval miss (the important one).** The answer IS in the corpus (Policy Manual: volunteer/unpaid work is allowed if 20+ hrs/week and field-related — Q4 even used it), but vector search surfaced STEM/DHS chunks instead, so the model never saw it and refused. → hybrid retrieval (BM25 + vector) + reranking.
- **Q9, Q12, Q14 — corpus coverage gaps.** Travel, self-employment, and multiple-employer rules aren't crisply covered by the 7 federal docs; refusing is the safe behavior. → expand the corpus.
- **Q13 — faithfulness error.** Answered + cited but wrong: it claimed a student may keep working while an *initial* post-completion OPT is pending (you can't — no work before the EAD). → anti-inference prompt rule (added in generate.py) + an answer-faithfulness check in Week 2.

---

### Q1. How many days of unemployment am I allowed on post-completion OPT?

- If you received initial post-completion OPT only, you may be unemployed for up to 90 days during the OPT period [source: https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt].
- If you received the 24-month extension, you may be unemployed for an additional 60 days, for a total of 150 days during the OPT period [source: https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt].

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5

### Q2. Can I start working before my EAD start date?

No, you may not start working before your Employment Authorization Document (EAD) start date. You must wait until the date indicated on your EAD to begin your employment [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5]. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/i-765, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5

### Q3. When can I apply for post-completion OPT?

You can apply for post-completion Optional Practical Training (OPT) under the following conditions:

- You must apply after your Designated School Official (DSO) enters the recommendation for OPT into your SEVIS (Student and Exchange Visitor Information System) record [source: https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students].
- You may apply up to 90 days before your program end date [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].
- You must apply no later than 60 days after your program end date [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].
- You must file your Form I-765 within 30 days of the date that your DSO enters the recommendation for OPT into your SEVIS record [source: https://www.uscis.gov/i-765].

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/i-765

### Q4. Does part-time work count toward maintaining OPT status?

Yes, part-time work does count toward maintaining OPT status. For post-completion OPT, students must work at least 20 hours per week, which qualifies as part-time employment [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5]. Additionally, students can work as volunteers or unpaid interns, provided the work is related to their program of study and does not violate any labor laws [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5]. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students

### Q5. How long is the grace period after my OPT ends?

An F-1 student who has completed an authorized period of post-completion OPT may remain in F-1 status for 60 days beyond the EAD (Employment Authorization Document) expiration date. This is commonly known as a grace period [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5]. 

During this grace period, the F-1 student may prepare for departure from the United States or take other actions such as contacting their DSO (Designated School Official) to change their education level, transfer to another SEVP (Student and Exchange Visitor Program)-certified school, or file an application or petition with USCIS to change to another nonimmigrant or immigrant status [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5

### Q6. How long is the STEM OPT extension, and who's eligible?

The STEM OPT (Optional Practical Training) extension is 24 months long. To be eligible for this extension, an F-1 student must meet the following criteria:

- Have been granted OPT and currently be in a valid period of post-completion OPT [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].
- Have earned a bachelor's, master's, or doctoral degree from a school that is accredited by a U.S. Department of Education-recognized accrediting agency and is certified by the Student and Exchange Visitor Program (SEVP) at the time of application [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].
- Not be in a multiple employer arrangement, or employed by a sole proprietorship, through a temp agency, or through a consulting firm arrangement that provides labor for hire [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].
- Be employed for no less than 20 hours per week by each qualifying STEM OPT employer [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].
- Complete an individualized Training Plan for STEM OPT Students (Form I-983) [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5

### Q7. Do I need a job offer to apply for OPT?

No, you do not need a job offer to apply for Optional Practical Training (OPT). You can apply for OPT even if you do not have a job offer at the time of your application [source: https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students]. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/i-765

### Q8. How soon must I report a change of employer?

You must report a change of employer to your Designated School Official (DSO) within 10 days of the change [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5]. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students

### Q9. Can I travel internationally while on OPT?

I don't have that in my official sources - please confirm with your DSO. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt

### Q10. What is cap-gap?

Cap-gap refers to the period during which certain F-1 students with a pending or approved cap-subject H-1B petition can remain in F-1 status and continue their employment authorization. This extension fills the "gap" between the expiration of F-1 status and the beginning of H-1B status, which typically starts on October 1 of the following fiscal year. The cap-gap period begins when the F-1 student's status and employment authorization expire and ends on October 1, unless terminated earlier [source: https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students]. 

To qualify for a cap-gap extension, the following conditions must be met:
- The F-1 student must be currently authorized for Optional Practical Training (OPT) employment.
- The student must not have violated the terms and conditions of their nonimmigrant status.
- The H-1B petition must have been timely filed.
- The petition must request an H-1B employment start date of October 1 of the following fiscal year [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5].

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students, https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students

### Q11. Can I do volunteer or unpaid work to avoid unemployment days?

I don't have that in my official sources - please confirm with your DSO. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt

### Q12. Is self-employment allowed on OPT?

I don't have that in my official sources - please confirm with your DSO. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5

### Q13. What happens if my program ends while my OPT application is still pending?

If your program ends while your Optional Practical Training (OPT) application is still pending, you may remain in F-1 status as long as you have a timely filed application. You can continue to work until USCIS makes a decision on your OPT application. If your application is denied, your F-1 status will expire 60 days from the date your degree program ends or the date of the denial, whichever is later [source: https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5]. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5

### Q14. Can I work for more than one employer on OPT?

I don't have that in my official sources - please confirm with your DSO. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students

### Q15. Does my OPT job have to relate to my major?

Yes, all Optional Practical Training (OPT) employment must be directly related to your major area of study [source: https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students]. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students, https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt

### Q16. What is the capital of France?

I don't have that in my official sources - please confirm with your DSO. 

This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney.

_retrieved:_ https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/students-and-employment, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5, https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/f-1-optional-practical-training-opt, https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students, https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5
