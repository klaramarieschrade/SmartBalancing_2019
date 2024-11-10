#vorgegeben: f_soll = 50Hz, P_me_0, P_el_0, Austauschleistungen zwischen Regelzonen P_A_soll, P_A_ist
#Regelungen: Primärregelung FCR, Sekundärregelung aFRR, Tertiärregelung mFRR + Selbstregeleffekt, Momentanreserve
#Ergebnis: f_ist
#Regelgröße: f_ist
#Stellgröße: P_FCR, P_aFRR, P_mFRR, Summe der unterschiedlichen Leistungen


'''
TODO: Implementation summarisches Netzmodell
1. Primärregelung FCR: P_FCR_soll = P_FCR_0 + K_p * (f_soll - f_ist)
    - Strecke: P_FCR_ist durch Verzögerung von P_FCR in queue realisiert
2. Selbstregeleffekt: delta_P_l = K_L*delta_f
3. Sekundärregelung aFRR: --> für jeden Regelzone
    - Berechnung ACE (beschreibt alle ungeplanten Lastflüsse über Grenze der CA), 
    - im Modell entspricht ACE = FRCE_ol (= P_me_soll - Pe_me + P_el - P_el_soll) 
    - Regelereingang im Modell: FRCE_cl_pos = FRCE_ol_pos - P_aFRR_pos bzw. FRCE_cl_neg = FRCE_ol_neg - P_aFRR_neg
        -  = P_A_ist - P_A_soll - K_Netz*delta_f 
        --> stellt Reglereingang dar, K_Netz = K_PRL + K_L der jeweiligen Regelzone
    - Sekundärregelung: P_aFRR_soll = -K_P*ACE - K_P/T_i *intergral(ACE)
    - Strecke: P_aFRR_ist durch Verzögerung von P_aFRR_soll in queue realisiert
    - aus berechneter Leistung werden Kosten, Preis und AEP berechnet, die an BK übermittelt werden, die darauf basierend über smart balancing entscheiden
4. Berechnung der Frequenz
    - delta_P = P_PRL_ist + P_me0 + P_l - P_el0 + P_aFRR_ist 
    - f_ist = f_0/P_0 * 1/(T_N * s) --> Zusammenhang zwischen Frequenz und Leistung durch Integrator beschreiben
5. Berücksichtigen des Beitrags vom Smart Balancing und eventuell mFRR
    - hat Einfluss auf ACE und so auf aFRR
    - hier: Entscheidungsfindung in class BalancingGroup und Höhe der Passive Balancing Leistung P_PB definiert
    - bekommt ACE, AEP, day-ahead Preis jeder ISP in Echtzeit übermittelt --> individuelle Entscheidung über Bereitstellung von P_PB je Bilanzkreis
    - führt zu Abweichung von Fahrplan in BK und so auch zu Abweichung in Regelzone und aFRR

'''
