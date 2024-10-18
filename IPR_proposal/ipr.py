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

    @property
    def outflows(self):
        out = []
        for item in self.inflows:
            if item.asset in self.retention_ratios.keys():
                out.append(Value(amount=item.amount * self.retention_ratios[item.asset],
                                      asset=item.asset,
                                      asset_price_ada=item.asset_price_ada))
            else:
                out.append(item)

        return out 

    @property
    def increase(self):
        return [i_in - i_out for i_in in self.inflows for i_out in self.outflows if i_in.asset==i_out.asset]

if __name__=="__main__":

    indy_price_ada = 1.9
    sp_indy_sell_ratio = 0.5
    sp_iasset_sell_ratio = 0.2
    sp_indy_emissions_pe = 18636.36

    sp_indy_emissions_pe = Value(amount=18636.36,
                                asset='indy',
                                asset_price_ada=indy_price_ada)

    sp = Body(inflows=[sp_indy_emissions_pe],
            retention_ratios ={'indy': 0.55, 'iUSD': 0.8})
    
    ada = Value(amount=100,
                asset='ada',
                asset_price_ada=1.0)

    iUSD = Value(amount=100,
                asset='iUSD',
                asset_price_ada=2.52)
    print(sp_indy_emissions_pe)
    print(sp_indy_emissions_pe.value_in(iUSD))
    print(sp.outflows)
    print(sp.increase)

    sp_indy_sold_pe = sp_indy_emissions_pe.amount * sp_indy_sell_ratio
    sp_indy_retained_pe = sp_indy_emissions_pe.amount - sp_indy_sold_pe 

    ada_revenue_pm = 1_000_000 
    ada_revenue_pe = ada_revenue_pm / 6
    ipr_funding_perc = 0.3
    ipr_iasset_purchased_pe_ada_value = ada_revenue_pe * ipr_funding_perc
    ipr_iasset_purchased_pe_indy_value = ipr_iasset_purchased_pe_ada_value / indy_price_ada

    print(f'--------Per Epoch----------\nsp emissions: {sp_indy_emissions_pe}\nsp sold: {sp_indy_sold_pe}\ndao repurchased: {ipr_iasset_purchased_pe_indy_value}')

    