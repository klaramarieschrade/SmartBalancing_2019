# ----------------------------------------------------------------------------------------------------------------------
# --- CLASS DEFINITION FOR BALANCING GROUPS ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

import fuzzlogi_marketdesign
import math

# Objects of class 'BalancingGroups' represent the Balancing Groups of a Control Area.
# 'BalancingGroups' are to be subordinated to objects of class 'ControlArea' only.
# In turn, any object of class 'ControlArea' needs subordinated 'BalancingGroups' to function properly.
class BalancingGroup:

    # CONSTRUCTOR METHOD
    # The constructor method is called to create an object of this class.
    # In the construction of an object of this class, all following variables are initialized...
    def __init__(self, name, read, smart):

        # ...Initialization of name
        self.name = name
        self.read = read
        self.smart = smart

        # ...Definition of load flow parameters
        self.gen_P = 0.0
        self.load_P = 0.0
        self.gen_P_schedule = self.gen_P
        self.load_P_schedule = self.load_P
        self.imba_P_ph = 0.0
        self.imba_P_sc = 0.0
        self.sb_P = 0.0
        self.sb_P_activate = 0.0

        # ...Definition of produced and consumed energies
        self.gen_E = 0.0
        self.load_E = 0.0
        self.gen_E_schedule = self.gen_E
        self.load_E_schedule = self.load_E
        self.imba_E = 0.0
        self.sb_E_pos = 0.0
        self.sb_E_neg = 0.0
        self.sb_E_pos_period = 0.0
        self.sb_E_neg_period = 0.0

        self.gen_E_period = 0.0
        self.load_E_period = 0.0
        self.gen_E_schedule_period = self.gen_E
        self.load_E_schedule_period = self.load_E
        self.imba_E_period = 0.0

        # ...Definition of AEP cost variables
        self.AEP_costs = 0.0
        self.AEP_costs_period = 0.0
        self.sb_costs_pos = 0.0
        self.sb_costs_neg = 0.0
        self.sb_costs_pos_period = 0.0
        self.sb_costs_neg_period = 0.0

        # ...Variables for energy costs and imcome
        self.gen_income = 0.0
        self.load_costs = 0.0
        self.gen_income_period = 0.0
        self.load_costs_period = 0.0

        # ...Definition of arrays containing simulation results
        self.array_gen_P = []
        self.array_load_P = []
        self.array_gen_P_schedule = []
        self.array_load_P_schedule = []
        self.array_gen_E = []
        self.array_load_E = []
        self.array_gen_E_schedule = []
        self.array_load_E_schedule = []
        self.array_gen_E_period = []
        self.array_load_E_period = []
        self.array_gen_E_schedule_period = []
        self.array_load_E_schedule_period = []
        self.array_imba_P_ph = []
        self.array_imba_P_sc = []
        self.array_imba_E = []
        self.array_imba_E_period = []
        self.array_sb_P = []
        self.array_sb_P_activate = []
        self.array_sb_E_pos = []
        self.array_sb_E_neg = []
        self.array_sb_E_pos_period = []
        self.array_sb_E_neg_period = []
        self.array_sb_costs_pos = []
        self.array_sb_costs_neg = []
        self.array_sb_costs_pos_period = []
        self.array_sb_costs_neg_period = []
        self.array_AEP_costs = []
        self.array_AEP_costs_period = []
        self.array_gen_income = []
        self.array_load_costs = []
        self.array_gen_income_period = []
        self.array_load_costs_period = []

        # ...Definition of array containing all subordinated Power Plants and Loads
        self.array_generators = []
        self.array_loads = []

        # ...Definition of array containing Smart Balancing assets
        self.array_sb_assets = []

        # Arrays for positive and negative Smart Balancing assets
        self.array_sb_molpos = []
        self.array_sb_molneg = []

    def schedule_init(self):
        if self.read: #True
            self.gen_P_schedule = self.array_gen_P_schedule[1]
            self.load_P_schedule = self.array_load_P_schedule[1]
        else:
            self.gen_P_schedule = self.gen_P
            self.load_P_schedule = self.load_P

    def imba_calc(self):
        self.imba_P_ph = self.gen_P - self.load_P + self.sb_P
        self.imba_P_sc = self.gen_P - self.gen_P_schedule - self.load_P + self.load_P_schedule + self.sb_P

    def gen_calc(self):
        self.gen_P = 0.0
        for i in self.array_generators:
            self.gen_P += i.gen_P

    def load_calc(self):
        self.load_P = 0.0
        for i in self.array_loads:
            self.load_P += i.load_P

    # Method calculating the generated and consumed energy for the balancing group.
    # Scheduled energies are also calculated.
    # All energy variables have a version, that gets reset after each ISP
    def afrr_calc(self, t_now, t_step, t_isp, AEP):
        self.gen_E += self.gen_P * t_step / 3600
        self.load_E += self.load_P * t_step / 3600

        self.gen_E_schedule += self.gen_P_schedule * t_step / 3600
        self.load_E_schedule += self.load_P_schedule * t_step / 3600

        self.imba_E += self.imba_P_sc * t_step / 3600

        if self.sb_P > 0:
            self.sb_E_pos += self.sb_P * t_step / 3600
        elif self.sb_P < 0:
            self.sb_E_neg += self.sb_P * t_step / 3600
        else:
            pass

        if (t_now % t_isp) == 0:
            self.gen_E_period = 0.0
            self.load_E_period = 0.0
            self.gen_E_schedule_period = 0.0
            self.load_E_schedule_period = 0.0
            self.imba_E_period = 0.0
            self.sb_E_pos_period = 0.0
            self.sb_E_neg_period = 0.0

        self.gen_E_period += self.gen_P * t_step / 3600
        self.load_E_period += self.load_P * t_step / 3600

        self.gen_E_schedule_period += self.gen_P_schedule * t_step / 3600
        self.load_E_schedule_period += self.load_P_schedule * t_step / 3600

        self.imba_E_period += self.imba_P_sc * t_step / 3600

        if self.sb_P > 0:
            self.sb_E_pos_period += self.sb_P * t_step / 3600
        elif self.sb_P < 0:
            self.sb_E_neg_period += self.sb_P * t_step / 3600
        else:
            pass

        # in the last time step of each ISP, the costs for imbalances are calculated
        if ((t_now + t_step) % t_isp) == 0:
            self.aep_costs_calc(AEP)

    # Method that calculates the costs for imbalances at the end of an ISP...
    # ...using to the "Ausgleichsenergiepreis" (AEP)
    # This method should be called in the last time step of an ISP
    def aep_costs_calc(self, AEP):
        self.AEP_costs_period = - self.imba_E_period * AEP
        self.AEP_costs += self.AEP_costs_period

        self.sb_costs_pos_period = - self.sb_E_pos_period * AEP
        self.sb_costs_pos += self.sb_costs_pos_period

        self.sb_costs_neg_period = - self.sb_E_neg_period * AEP
        self.sb_costs_neg += self.sb_costs_neg_period

    def sb_init(self):
        array_name = []
        array_price = []
        array_power = []
        for i in self.array_sb_assets:
            if not array_price and i.sb_P_max > 0:
                array_name.append(i.name)
                array_price.append(i.sb_costs)
                array_power.append(i.sb_P_max)
            elif array_price and i.sb_P_max > 0:
                j = 0
                while j < len(array_price) and array_price[j] < i.sb_costs:
                    j += 1
                array_name.insert(j, i.name)
                array_price.insert(j, i.sb_costs)
                array_power.insert(j, i.sb_P_max)

        self.array_sb_molpos = {'SB Asset ID': array_name,
                                'Price': array_price,
                                'Power': array_power}

        array_name = []
        array_price = []
        array_power = []
        for i in self.array_sb_assets:
            if not array_price and i.sb_P_min < 0:
                array_name.append(i.name)
                array_price.append(i.sb_costs)
                array_power.append(i.sb_P_min)
            elif array_price and i.sb_P_min < 0:
                j = 0
                while j < len(array_price) and array_price[j] < i.sb_costs:
                    j += 1
                array_name.insert(j, i.name)
                array_price.insert(j, i.sb_costs)
                array_power.insert(j, i.sb_P_min)

        self.array_sb_molneg = {'SB Asset ID': array_name,
                                'Price': array_price,
                                'Power': array_power}

    # This method calculates the Smart Balancing power of the Smart Balancing Assets of the Balancing Group
    def sb_calc(self, FRCE_sb, old_FRCE_sb, d_Imba, old_d_Imba, AEP, t_step, t_now, da_price, windon_mmw, windoff_mmw, pv_mmw,
                FRR_E_pos_period, FRR_E_neg_period, fuzzy, imbalance_clearing,con_FRR_pos,con_FRR_neg):

        ## 25.10.2020 restructure sb_calc (FR)
        #  if smart -> imbalance clearing ("0" for single and "1" for combined/NL)
        # 1. sb_pot_calc() = individual SB potential in MW - see generato.py / loadload.py
        # 2. calculate sb_P, ask if fuzzy and call sb_activation() - see generato.py / loadload.py
        # 3.    if fuzzy -> manipulate sb_P with fuzzilogi_marketdesign.py
        # 4.    activate sb_P according to sb_activate (ramp max)- - see generato.py / loadload.py
        # SB remains if ACE between 200 MW and -200 MW
        # if FRCE_sb > -200 and FRCE_sb < 200:
        #    pass

        # smart not true: nothing happens
        if not self.smart:
            self.sb_P = 0.0

        #SB set back to zero at the end of each ISP
        #elif (t_now + t_step) % 900 == 0 and not self.sb_P == 0:
        #    SB_Asset_ID = []
        #    SB_per_asset = []
        #    for i in self.array_sb_assets:
        #        SB_Asset_ID.append(i.name)
        #        SB_per_asset.append(0.0)

        else:  # smart true: Activation of SB Assets using Fuzzy Logic (if fuzzy = true)
            SB_Asset_ID = []
            SB_per_asset = []

            # Calc time within 15 Min ISP in Minute (between 0 and 14) for fuzzy and p_average
            time_in_ISP = (t_now / 60) % 15
            # todo: fair to compare FRCE_sb (ol) with p_average ?
            # calc p_average in MW in ISP for fuzzy (from FRR of ISP in MWh)
            p_average = (FRR_E_pos_period + FRR_E_neg_period) / ((time_in_ISP + 1) / 60)

            if not FRCE_sb == 0:
                    if (self.sb_P/FRCE_sb) < 0:
                        over_reaction = True
                    else:
                        over_reaction = False
            else:
                over_reaction = False

            # SB is reset at the end of an ISP or if dual price applies with combined pricing
            # todo: make t_isp available and replace 900
            # todo: make condition for dual price (conter-activation of 5 MWh) a global variable
            if (((t_now + t_step) % 900) == 0) or (imbalance_clearing == 1 and (FRR_E_neg_period < -5) and (FRR_E_pos_period > 5)):  # and not (self.sb_P == 0):
                #check if ISP end is reached -> SB back to zero
                #print("self.name: ",self.name,' und self.sb_P: ',self.sb_P,' und t_now: ',t_now)
                for i in self.array_sb_assets:
                    SB_Asset_ID.append(i.name)
                    SB_per_asset.append(0.0)

            # SB with single pricing: sb_P remains the same, if p_average close to zero
            elif imbalance_clearing == 0 and (300 > p_average and p_average > -300):
                pass

            # Smart Balancing with combined pricing: remains the same, if no over-reaction and FRCE "close to zero"
            elif imbalance_clearing == 1 and not over_reaction and (300 > FRCE_sb and FRCE_sb > -300):
                pass

            # traffic light approaches (TL3 and TL6): SB is activated only once until the end of an ISP
            elif (imbalance_clearing == 2 or imbalance_clearing == 3) and (self.sb_P < -10.0 or self.sb_P > 10.0):
                pass

        # in all other cases: individual SB calculation
            else:
                # 1. The positive and negative SB potentials of all assets get updated. - see generato.py / loadload.py
                for i in self.array_sb_assets:
                    i.sb_pot_calc()

                # 2. Summation of the total positive and negative Smart Balancing potential of the Balancing Group
                # Variables can get used to prevent overshoots in case of FRCE_sb close to zero
                P_max_sum = 0.0
                P_min_sum = 0.0
                for i in self.array_sb_assets:
                    P_max_sum += i.sb_pot_pos
                    P_min_sum += i.sb_pot_neg

                sb_sum = 0.0
                pos_margin = 0
                neg_margin = 0
                FRR_ratio = 1
                sb_marge = 1

                for i in self.array_sb_assets:
                    if self.name == 'Solar' or self.name == 'Wind_Onshore' or self.name == 'Wind_Offshore':
                        #min margin for reducing solar or wind generation, must be negative!
                        neg_margin = -40
                        #"Monatsmarktwert" (to calculate individual feed in tariff)
                        if self.name == 'Solar':
                            mmw = pv_mmw
                        elif self.name == "Wind_Onshore":
                            mmw = windon_mmw
                        elif self.name == "Wind_Offshore":
                            mmw = windoff_mmw
                        else:
                            pass

                        # "Marktprämie" (EE losing money, if "anzulegender Wert" (i.sb_c.) is higher "Marktmonatswert"(mmw)
                        if i.sb_costs - mmw > 0:
                            neg_margin += -i.sb_costs + mmw

                    elif self.name == "Aluminium":
                        pos_margin = 100 + da_price

                    elif self.name == 'Steel':
                        pos_margin = 250 + da_price

                    elif self.name == 'Cement' or self.name == 'Paper' or self.name == 'Chlorine':
                        pos_margin = 100 + da_price
                        neg_margin = 10

                    elif self.name == 'Group_Gas':
                        pos_margin = i.sb_costs + 15
                        neg_margin = i.sb_costs - 35

                    else:
                        pos_margin = i.sb_costs
                        neg_margin = i.sb_costs

                    # Decision making for Balancing Group, with individual neg_ and pos_potential
                    #decision making with traffic light approach (no AEP known)
                    if (imbalance_clearing == 2 or imbalance_clearing == 3):
                        if FRCE_sb < 0 and con_FRR_neg < 0:
                            FRR_ratio = FRCE_sb/con_FRR_neg * 100
                            if (imbalance_clearing == 2 and FRR_ratio > 0.8) or (imbalance_clearing == 3 and FRR_ratio > 0.6):
                                if fuzzy:
                                    sb_percent = fuzzlogi_marketdesign.fuzz(sb_marge, FRCE_sb, old_FRCE_sb, old_d_Imba,
                                                                            d_Imba,
                                                                            time_in_ISP,
                                                                            p_average, imbalance_clearing, self.sb_P,
                                                                            P_min_sum, FRR_ratio)
                                    sb_activation = i.sb_pot_neg * sb_percent
                                else:
                                    sb_activation = i.sb_pot_neg
                            else:
                                sb_activation = 0.0
                        elif FRCE_sb > 0 and con_FRR_pos > 0:
                            FRR_ratio = FRCE_sb/con_FRR_pos * 100
                            if (imbalance_clearing == 2 and FRR_ratio > 0.8) or (imbalance_clearing == 3 and FRR_ratio > 0.6):
                                if fuzzy:
                                    sb_percent = fuzzlogi_marketdesign.fuzz(sb_marge, FRCE_sb, old_FRCE_sb, old_d_Imba,
                                                                            d_Imba,
                                                                            time_in_ISP,
                                                                            p_average, imbalance_clearing, self.sb_P,
                                                                            P_min_sum, FRR_ratio)
                                    sb_activation = i.sb_pot_pos * sb_percent
                                else:
                                    sb_activation = i.sb_pot_pos
                            else:
                                sb_activation = 0.0
                        else:
                            sb_activation = 0.0

                    # decision making with transparent approach (AEP und FRCE known)
                    elif AEP < neg_margin and i.sb_pot_neg < 0:
                        if fuzzy:
                            sb_marge = -AEP + neg_margin
                            sb_percent = fuzzlogi_marketdesign.fuzz(sb_marge, FRCE_sb, old_FRCE_sb, old_d_Imba, d_Imba,
                                                                    time_in_ISP,
                                                                    p_average, imbalance_clearing, self.sb_P,
                                                                    P_min_sum,FRR_ratio)
                            sb_activation = i.sb_pot_neg * sb_percent
                        else:
                            sb_activation = i.sb_pot_neg

                    elif AEP > pos_margin and i.sb_pot_pos > 0:
                        if fuzzy:
                            sb_marge = AEP - pos_margin
                            sb_percent =fuzzlogi_marketdesign.fuzz(sb_marge, FRCE_sb, old_FRCE_sb, old_d_Imba, d_Imba,
                                                                    time_in_ISP,
                                                                    p_average, imbalance_clearing, self.sb_P,
                                                                    P_max_sum,con_FRR_pos)
                            sb_activation = i.sb_pot_pos * sb_percent
                        else:
                            sb_activation = i.sb_pot_pos
                    else:
                        sb_activation = 0.0

                    # Optional limitation of the targeted Smart Balancing power using the total FRCE
                    # sb_sum could be used here, it represents already activated SB within Balagroup
                    # cost optimized activation, if assetts are in correct order (MOL)
                    # limitation of positive SB
                    limit = 3
                    if (sb_activation +sb_sum) > 0:
                        if imbalance_clearing == 0 and p_average > 0:
                            if (sb_activation +sb_sum) > (p_average / limit):
                                sb_activation = (p_average / limit) - sb_sum
                        elif imbalance_clearing == 1 and FRCE_sb > 0:
                            if (sb_activation +sb_sum) > (FRCE_sb / limit):
                                sb_activation = (FRCE_sb / limit) - sb_sum
                        else:
                            sb_activation = sb_activation / 4  # over-reaction already in place. reduction of SB
                    # limitation of negative SB
                    elif (sb_activation +sb_sum) < 0:
                        if imbalance_clearing == 0 and p_average < 0:
                            if (sb_activation +sb_sum) < (p_average / limit):
                                sb_activation = (p_average / limit) - sb_sum
                        elif imbalance_clearing == 1 and FRCE_sb < 0:
                            if (sb_activation +sb_sum) < (FRCE_sb / limit):
                                sb_activation = (FRCE_sb / limit) - sb_sum
                        else:
                            sb_activation = sb_activation / 4  #over-reaction already in place. reduction of SB
                    else:
                        pass

                    SB_Asset_ID.append(i.name)
                    SB_per_asset.append(sb_activation)
                    sb_sum += sb_activation



            # 4.    activate sb_P according to sb_activate (ramp max)- - see generato.py / loadload.py
            # > see sb_activate() in generator.py / loadload.py
            array_sb_activate = {"SB_Asset_ID": SB_Asset_ID, "SB_per_asset": SB_per_asset}
            j = 0
            while j <= len(array_sb_activate['SB_Asset_ID']) - 1:
                for i in self.array_sb_assets:
                    if array_sb_activate.get('SB_Asset_ID')[j] == i.name:
                        i.sb_activate(array_sb_activate.get('SB_per_asset')[j], t_step,FRCE_sb,p_average,imbalance_clearing)
                j += 1
            #calculate total sb_P of Balagroup (all SB assets)
            self.sb_P = 0.0
            for i in self.array_sb_assets:
                self.sb_P += i.sb_P

    # Method calculating the costs for consumed energy and the income of produced energy of the grid element.
    # The method multiplies the consumed and produced amounts of energy per t_step with the current day-ahead price
    def energy_costs_calc(self, k_now, t_now, t_step, t_isp, da_price, windon_mmw, windoff_mmw, pv_mmw):
        # Calculation of income for Balancing Groups "Solar", "Wind_Onshore", and "Wind_Offshore"
        # Using the "Marktprämie" (mp) for each generator
        if self.name == "Solar":
            for i in self.array_sb_assets:
                mp = i.sb_costs - pv_mmw
                if mp < 0:
                    mp = 0.0
                else:
                    pass
                self.gen_income += (i.gen_P + i.sb_P) * mp * t_step / 3600

        elif self.name == "Wind_Onshore":
            for i in self.array_sb_assets:
                mp = i.sb_costs - windon_mmw
                if mp < 0:
                    mp = 0.0
                else:
                    pass
                self.gen_income += (i.gen_P + i.sb_P) * mp * t_step / 3600

        elif self.name == "Wind_Offshore":
            for i in self.array_sb_assets:
                mp = i.sb_costs - windoff_mmw
                if mp < 0:
                    mp = 0.0
                else:
                    pass
                self.gen_income += (i.gen_P + i.sb_P) * mp * t_step / 3600

        # Calculation of costs and income for other Balancing Groups
        else:
            self.gen_income += self.gen_P_schedule * da_price * t_step / 3600
            self.load_costs += self.load_P_schedule * da_price * t_step / 3600




        # Calculation of costs and income per ISP
        # Variables get set to zero after every ISP
        if (t_now % t_isp) == 0:
            self.gen_income_period = 0.0
            self.load_costs_period = 0.0

        # Calculation of income for Balancing Groups "Solar", "Wind_Onshore", and "Wind_Offshore"
        # Using the "Monatsmarktwert" and "anzulegender Wert" for each generator (GeneratorFlex)
        if self.name == "Solar":
            for i in self.array_sb_assets:
                mp = i.sb_costs - pv_mmw
                if mp < 0:
                    mp = 0.0
                else:
                    pass
                self.gen_income_period += (i.gen_P + i.sb_P) * mp * t_step / 3600

        elif self.name == "Wind_Onshore":
            for i in self.array_sb_assets:
                mp = i.sb_costs - windon_mmw
                if mp < 0:
                    mp = 0.0
                else:
                    pass
                self.gen_income_period += (i.gen_P + i.sb_P) * mp * t_step / 3600

        elif self.name == "Wind_Offshore":
            for i in self.array_sb_assets:
                mp = i.sb_costs - windoff_mmw
                if mp < 0:
                    mp = 0.0
                else:
                    pass
                self.gen_income_period += (i.gen_P + i.sb_P) * mp * t_step / 3600

        # Calculation of costs and income for other Balancing Groups for each ISP
        else:
            self.gen_income_period += self.gen_P_schedule * da_price * t_step / 3600
            self.load_costs_period += self.load_P_schedule * da_price * t_step / 3600

    def readarray(self, k_now):
        if self.read:
            self.gen_P_schedule = self.array_gen_P_schedule[k_now]
            self.load_P_schedule = self.array_load_P_schedule[k_now]
        for i in self.array_generators:
            i.readarray(k_now=k_now)
        for i in self.array_loads:
            i.readarray(k_now=k_now)

    def write_results(self):
        for i in self.array_generators:
            i.write_results(type='gen')
        for i in self.array_loads:
            i.write_results(type='load')
        for i in self.array_sb_assets:
            i.write_results(type='sb')
        self.array_gen_P.append(self.gen_P)
        self.array_load_P.append(self.load_P)
        if not self.read:
            self.array_gen_P_schedule.append(self.gen_P_schedule)
            self.array_load_P_schedule.append(self.load_P_schedule)
        self.array_gen_E.append(self.gen_E)
        self.array_load_E.append(self.load_E)
        self.array_gen_E_schedule.append(self.gen_E_schedule)
        self.array_load_E_schedule.append(self.load_E_schedule)
        self.array_gen_E_period.append(self.gen_E_period)
        self.array_load_E_period.append(self.load_E_period)
        self.array_gen_E_schedule_period.append(self.gen_E_schedule_period)
        self.array_load_E_schedule_period.append(self.load_E_schedule_period)
        self.array_imba_P_ph.append(self.imba_P_ph)
        self.array_imba_P_sc.append(self.imba_P_sc)
        self.array_imba_E.append(self.imba_E)
        self.array_imba_E_period.append(self.imba_E_period)
        self.array_sb_P.append(self.sb_P)
        self.array_sb_P_activate.append(self.sb_P_activate)
        self.array_sb_E_pos.append(self.sb_E_pos)
        self.array_sb_E_neg.append(self.sb_E_neg)
        self.array_sb_E_pos_period.append(self.sb_E_pos_period)
        self.array_sb_E_neg_period.append(self.sb_E_neg_period)
        self.array_AEP_costs.append(self.AEP_costs)
        self.array_AEP_costs_period.append(self.AEP_costs_period)
        self.array_sb_costs_pos.append(self.sb_costs_pos)
        self.array_sb_costs_neg.append(self.sb_costs_neg)
        self.array_sb_costs_pos_period.append(self.sb_costs_pos_period)
        self.array_sb_costs_neg_period.append(self.sb_costs_neg_period)
        self.array_gen_income.append(self.gen_income)
        self.array_load_costs.append(self.load_costs)
        self.array_gen_income_period.append(self.gen_income_period)
        self.array_load_costs_period.append(self.load_costs_period)
