# Criterii de selecție a cazului B (înghețate)

Politomorphism Research Project. Se face commit și se înregistrează hash-ul SHA-256 al acestui fișier și al `cases.json` **înainte** de orice serie SRM sau C. Pragurile sunt convenții, scrise acum, neschimbate după ce se văd datele.

Principiu: lista de candidați se generează mecanic. Criteriile A-C folosesc doar fapte juridice și de calendar, nu rezonanță sau vizualizări. România (origine 6 decembrie 2024) rămâne cazul A, închis ca netestabil (N_pre = 9 zile), și se raportează alături de B.

## A. Actul

1. Actul este o excludere formală a unui simbol (persoană, partid, candidatură, interdicție de media) printr-o decizie a unei autorități competente, cu dată publică verificabilă.
2. Actul primar este primul act obligatoriu care scoate simbolul din circuitul legal. Decizia care închide calea de atac este test de robustețe, nu test principal. Regula se aplică identic tuturor cazurilor.
3. Excluse: proceduri penale obișnuite pe fapte fără legătură cu rolul politic (separate de index, ca în nota privind România).
4. Niciun alt act de excludere asupra aceluiași simbol în cele 26 de săptămâni dinaintea actului primar (`prior_act_in_26w = false`, declarat în `cases.json` cu sursă).

## B. Fereastra

1. Cel puțin 26 de săptămâni (182 de zile) de expunere măsurabilă înainte de act, socotite de la `exposure_start`, și cel puțin 182 de zile după, cu tranziția (±3 zile) exclusă.
2. `exposure_start` este un fapt de calendar cu sursă (primul eveniment datat care creează expunerea sau încheie un șoc anterior). Nu se alege din forma seriei de vizualizări.
3. Baza de normalizare: mediana vizualizărilor pe 52 de săptămâni care se termină cu 90 de zile înainte de act. Fixată din calendar.
4. Verificare cu `audit_fezabilitate_v2.py` pe N_pre, N_post și MDE, nu pe mărimea vizualizărilor.

## C. Controlul

1. Cel puțin două simboluri neexcluse în același sistem politic și aceeași perioadă. Lista se scrie înainte de orice serie post-act.
2. Potrivire pe expunerea pre-act: raportul medianelor de vizualizări în fereastra pre-act, între simbolul exclus și fiecare control, în intervalul [1/3, 3].
3. Rol comparabil (candidat vs. candidat, partid vs. partid).

## D. Seria C (verificată manual, doar pentru candidații care trec de A-C)

1. Corpus disjunct de cel al SRM, cu cel puțin 30 de documente pe săptămână care menționează simbolul, în pre și în post. Altfel săptămâna se marchează lipsă.
2. Codebook înghețat și hash-uit, codare oarbă la SRM și la data actului, alfa Krippendorff ≥ 0,67 pe eșantionul dublu-codat, ca prag de intrare.
3. Alternativă: microdate de sondaj cu același item și aceeași formulare în cel puțin 8 valuri pre și 8 post. Altfel nu intră.

## E. Stabilitatea lui SRM (verificată manual)

Abaterea standard a lui SRM în fereastra post trebuie să fie cel puțin jumătate din cea pre. Dacă SRM se prăbușește după act, panta nu se poate estima.

## F. Confundantul de platformă

Pentru fiecare caz se codează binar, în avans (`platform_removal`), dacă a existat eliminare de conținut sau suspendare de cont în jurul actului. Cazul intră oricum; δ se raportează separat pe cele două grupuri.

## G. Procedura de selecție

1. Candidații se adună dintr-o sursă numită înainte de căutare (câmpul `source` din `cases.json`), nu din memorie. Cazurile în care excluderea nu a produs efectul așteptat sunt incluse obligatoriu.
2. Criteriile se aplică în ordinea A, B, C, D, E. Fiecare respingere se înregistrează cu motiv (`results/audit_results.csv`).
3. Dacă trec mai multe cazuri, alegerea se face prin cea mai veche dată a actului sau prin tragere la sorți cu seed fix (20261011). Nu prin rezonanță sau familiaritate.
4. Tabelul candidat-criteriu se hash-uiește înainte de orice date SRM sau C.

## Ce spune și ce nu spune un „TESTABIL"

Scriptul verifică numai B și potrivirea de la C.2, plus puterea (MDE). A, C.1, C.3, D, E și F sunt declarații sau verificări manuale. „TESTABIL" înseamnă „merită să ceri seria C", nu „δ este estimabil".
