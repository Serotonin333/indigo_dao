import numpy as np
    
if __name__=="__main__":
    indy_price_ada = 1.9
    sp_indy_sell_ratio = 0.5
    sp_iasset_sell_ratio = 0.2
    sp_indy_emissions_per_epoch = 18636.36
    sp_indy_sold_per_epoch = sp_indy_emissions_per_epoch * sp_indy_sell_ratio

    ada_revenue_per_epoch = 1_000_000 / 6
    ipr_funding_perc = 0.3
    ipr_iasset_purchased_ada_value = ada_revenue_per_epoch * ipr_funding_perc
    ipr_iasset_purchased_indy_value = ipr_iasset_purchased_ada_value / indy_price_ada

    print(f'--------Per Epoch----------\nsp emissions: {sp_indy_emissions_per_epoch}\nsold: {sp_indy_sold_per_epoch}\nrepurchase: {ipr_iasset_purchased_indy_value}')
