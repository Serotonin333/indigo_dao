import numpy as np
from dataclasses import dataclass
# pe: per epoch
# pm: per month

@dataclass
class Value:
    amount: float
    asset: str
    asset_price_ada: float | None = None

    @property
    def value_ada(self):
        return self.amount * self.asset_price_ada

    @property
    def asset_inv_price_ada(self) -> float:
        return 1/self.asset_price_ada

    def __add__(self, val):
        if self.asset == val.asset:
            total = self.amount + val.amount
            return Value(amount=total,
                         asset=self.asset, 
                         asset_price_ada=(self.value_ada - val.value_ada)/total)
        else:
            total = self.value_ada + val.value_ada
            return Value(amount=total,
                         asset='ada',
                         asset_price_ada=1.0)
    
    def __sub__(self, val):
        if self.asset == val.asset:
            total = self.amount - val.amount
            return Value(amount=total,
                         asset=self.asset, 
                         asset_price_ada=(self.value_ada - val.value_ada)/total)
        else:
            total = self.value_ada - val.value_ada
            return Value(amount=total,
                         asset='ada',
                         asset_price_ada=1.0)

    def value_in(self, asset):
        if type(self) == type(asset):
            amount = self.value_ada / asset.asset_price_ada
            return Value(amount=amount,
                         asset=asset.asset,
                         asset_price_ada=asset.asset_price_ada)


@dataclass
class Body:
    inflows: list[Value]
    retention_ratios: dict
    name: str | None = None

    @property
    def outflows(self):
        out = []
        for item in self.inflows:
            if item.asset in self.retention_ratios.keys():
                out.append(Value(amount=item.amount * (1.0 - self.retention_ratios[item.asset]),
                                      asset=item.asset,
                                      asset_price_ada=item.asset_price_ada))
            else:
                out.append(item)

        return out 

    @property
    def increase(self):
        return [i_in - i_out for i_in in self.inflows for i_out in self.outflows if i_in.asset==i_out.asset]
    
    @property
    def inflows_str(self):
        head = "__Inflow__\n"
        text = ""
        for i in self.inflows:
            text = text + f'{i.asset}: {i.amount} ({i.value_ada} ADA)\n'
        
        return head + "-0-" if text == "" else head + text
    
    @property
    def outflows_str(self):
        head = "__Outflow__\n"
        text = ""
        for o in self.outflows:
            text = text + f'{o.asset}: {o.amount} ({o.value_ada} ADA)\n'
        return head + "-0-" if text == "" else head + text

    def __repr__(self):
        return f'----{self.name}----\n{self.inflows_str}\n{self.outflows_str}'


def current_scenario():

    return sp, dao_treasury
if __name__=="__main__":
    # Current Scenario
    indy_price_ada = 1.9
    iUSD_price_ada = 2.5
    sp_indy_sell_ratio = 0.5
    sp_iasset_sell_ratio = 0.2
    sp_indy_emissions_pe = 18636.36
    sp_retention_ratios = {'indy': 0.55, 'iUSD': 0.8}
    dao_treasury_retention_ratios = {'indy':1.0, 'ada': 1.0, "iUSD": 0.0}
    sp_indy_emissions_pe = Value(amount=18636.36,
                                asset='indy',
                                asset_price_ada=indy_price_ada)

    sp = Body(inflows=[sp_indy_emissions_pe],
            retention_ratios = sp_retention_ratios,
            name="Stability Pool")
    
    ada = Value(amount=100,
                asset='ada',
                asset_price_ada=1.0)

    iUSD = Value(amount=100,
                asset='iUSD',
                asset_price_ada=2.52)
    
    dao_interest_ada_pm = 500_000 
    dao_interest_ada_pe = dao_interest_ada_pm / 6
    dao_indy_buyback_perc = 0.3
    dao_indy_buybacks_pe = Value(amount=dao_interest_ada_pe * dao_indy_buyback_perc / indy_price_ada,
                                 asset="indy",
                                 asset_price_ada=indy_price_ada)
    dao_treasury = Body(inflows=[dao_indy_buybacks_pe], retention_ratios=dao_treasury_retention_ratios, name="DAO Treasury")

    print(sp)
    print(dao_treasury)

    # Proposed Scenario
    ipr_funding_perc = 0.3
    ipr_retention_ratios = {'indy': 1.0, 'ada': 1.0, 'iUSD': 0.0}
    max_ipr_purchase_pe_ada = sp_indy_emissions_pe.value_ada
    ipr_budget_pe_ada = ipr_funding_perc * dao_interest_ada_pe
    ipr_iUSD_buy_pe_ada = min(ipr_budget_pe_ada, max_ipr_purchase_pe_ada)
    ipr_excess_ada = max(0, ipr_budget_pe_ada - ipr_iUSD_buy_pe_ada)
    ipr_iUSD_purchase_pe = Value(amount=ipr_iUSD_buy_pe_ada/iUSD_price_ada, asset='iUSD', asset_price_ada=iUSD_price_ada)
    ipr_ada_in_pe = Value(amount=ipr_excess_ada, asset='ada', asset_price_ada=1.0)
    ipr = Body(inflows=[ipr_iUSD_purchase_pe, ipr_ada_in_pe], retention_ratios=ipr_retention_ratios, name="Indigo Peg Reserve")
    
    sp_iUSD_pe = [a for a in ipr.outflows if a.asset=='iUSD'][0]
    sp_indy_income_ratio = (sp_indy_emissions_pe.value_ada - sp_iUSD_pe.value_ada) / sp_indy_emissions_pe.value_ada
    sp_indy_pe = Value(amount=sp_indy_emissions_pe.amount * sp_indy_income_ratio,
                       asset="indy",
                       asset_price_ada=indy_price_ada)
    sp = Body(inflows=[sp_iUSD_pe, sp_indy_pe], retention_ratios=sp_retention_ratios, name="Stability Pool")
    
    dao_indy_emissions_pe = Value(amount=ipr_iUSD_purchase_pe.value_ada / indy_price_ada,
                                  asset='indy',
                                  asset_price_ada=indy_price_ada)

    dao_treasury = Body(inflows=[dao_indy_emissions_pe], retention_ratios=dao_treasury_retention_ratios, name="DAO Treasury")

    print(ipr)
    print(sp)
    print(dao_treasury)    