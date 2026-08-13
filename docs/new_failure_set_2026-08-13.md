# New failure set (2026-08-13) — supersedes the old 79+79 classified set

Current pipeline: dedup-convention prompt fix + per-database hints removed +
timeout raised 60s→240s + `reasoning_effort=high`. Full 500-question result:
**351/500 = 70.20%**, 0 timeouts.

Compared against the old classification sheet (`transcripts/rhigh_500/classification_sheet.csv`,
158 questions, 79 Aziz / 79 Hanyan):
- **130 still failing** — same questions, presumably same root causes. Reuse
  the old classification as-is, no need to redo.
- **19 new failures** — never classified before. This is the fresh work,
  split below.
- **28 fixed** — used to fail, now pass. Listed below for reference; direct
  evidence the dedup fix works on real failures (8/13 classified ones are
  dedup-convention family), not just the controlled test set.

## New failures (19) — to split, ~9-10 each

| id | db_id | difficulty | question |
|---|---|---|---|
| bird_1028 | european_football_2 | challenging | In Scotland Premier League, which away team won the most during the 2010 season? |
| bird_1036 | european_football_2 | challenging | List the long name of teams with above-average build-up play passing in 2012. |
| bird_11 | california_schools | simple | Please list the codes of the schools with a total enrollment of over 500. |
| bird_1141 | european_football_2 | moderate | Does the KSV Cercle Brugge team have a slow, balanced or fast speed class? |
| bird_1187 | thrombosis_prediction | moderate | How many patients who were examined between 1987/7/6 and 1996/1/31 had a GPT level greater... |
| bird_1189 | thrombosis_prediction | challenging | What number of patients with a degree of thrombosis level 2 and ANA pattern of only S, hav... |
| bird_1257 | thrombosis_prediction | challenging | Among the patients whose creatinine level is abnormal, how many of them aren't 70 yet? |
| bird_17 | california_schools | simple | Rank schools by their average score in Writing where the score is greater than 499, showin... |
| bird_189 | financial | moderate | Name the account numbers of female clients who are oldest and have lowest average salary? |
| bird_201 | toxicology | moderate | What is the percentage of carbon in double-bond molecules? |
| bird_220 | toxicology | challenging | Please list top three elements of the toxicology of the molecule TR000 in alphabetical ord... |
| bird_245 | toxicology | moderate | What is the average number of bonds the atoms with the element iodine have? |
| bird_531 | codebase_community | simple | Which user has a higher reputation, Harlan or Jarrod Dixon? |
| bird_557 | codebase_community | moderate | Among the posts with a score of over 5, what is the percentage of them being owned by an e... |
| bird_77 | california_schools | moderate | Which schools served a grade span of Kindergarten to 9th grade in the county of Los Angele... |
| bird_800 | superhero | moderate | Calculate the percentage of superheroes with blue eyes. |
| bird_872 | formula_1 | simple | In the race No. 45, for the driver who had the Q3 time as 0:01:33, what is his abbreviated... |
| bird_892 | formula_1 | moderate | State the driver with the most points scored. Find his full name with that points. |
| bird_915 | formula_1 | simple | Which country is the oldest driver from? |

## Fixed (28) — reference only, no action needed

| id | db_id | difficulty | question |
|---|---|---|---|
| bird_1032 | european_football_2 | moderate | Give the name of the league with the highest matches of all time and how many matches were... |
| bird_1148 | european_football_2 | moderate | What is the percentage of players that are under 180 cm who have an overall strength of mo... |
| bird_1198 | thrombosis_prediction | simple | How many female patients were given an APS diagnosis? |
| bird_1227 | thrombosis_prediction | moderate | What is the average age of the male patient with high cholesterol? |
| bird_1255 | thrombosis_prediction | moderate | For the patients with an abnormal Ig M level, what is the most common disease they are dia... |
| bird_1256 | thrombosis_prediction | moderate | How many patients with a abnormal C-reactive protein don't have their data recorded? |
| bird_1267 | thrombosis_prediction | moderate | Among the patients with normal anti-SM, how many of them does not have thrombosis? |
| bird_1275 | thrombosis_prediction | moderate | Among the patients who has a normal level of anti-centromere and a normal level of anti-SS... |
| bird_1302 | thrombosis_prediction | challenging | For the patients with a normal range of creatinine phosphokinase, how many of them have a ... |
| bird_1490 | debit_card_specializing | moderate | How many percent of LAM customer consumed more than 46.73? |
| bird_1505 | debit_card_specializing | simple | Among the customers who paid in euro, how many of them have a monthly consumption of over ... |
| bird_1525 | debit_card_specializing | simple | What is the percentage of the customers who used EUR in 2012/8/25? |
| bird_23 | california_schools | moderate | List the names of schools with more than 30 difference in enrollements between K-12 and ag... |
| bird_260 | toxicology | moderate | Calculate the total atoms with triple-bond molecules containing the element phosphorus or ... |
| bird_263 | toxicology | challenging | What is the composition of element chlorine in percentage among the single bond molecules? |
| bird_36 | california_schools | challenging | Under whose administration is the school with the highest number of students scoring 1500 ... |
| bird_371 | card_games | challenging | What is the percentage of cards whose language is French among the Story Spotlight cards? |
| bird_383 | card_games | simple | How many of the banned cards are white border? |
| bird_41 | california_schools | simple | List the names of virtual schools that are among the top 5 in their respective counties ba... |
| bird_416 | card_games | challenging | What percentage of cards without power are in French? |
| bird_462 | card_games | moderate | What's the Italian name of the set of cards with "Ancestor's Chosen" is in? |
| bird_539 | codebase_community | simple | Who is the owner of the post "Eliciting priors from experts"? |
| bird_598 | codebase_community | challenging | What is the percentage difference of student badges given during 2010 and 2011? |
| bird_744 | superhero | challenging | Between DC and Marvel Comics, which publisher has published more superheroes? Find the dif... |
| bird_751 | superhero | moderate | List down at least five superpowers of male superheroes. |
| bird_829 | superhero | challenging | Which publisher created more superheroes: DC or Marvel Comics? Find the difference in the ... |
| bird_897 | formula_1 | moderate | Name the driver with the most winning. Mention his nationality and what is his maximum poi... |
| bird_978 | formula_1 | simple | How many times the circuits were held in Austria? Please give their location and coordinat... |
