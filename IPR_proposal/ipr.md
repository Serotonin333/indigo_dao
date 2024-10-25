# Proposal to Enact an Indigo Peg Reserve

This purpose of this discussion is to examine the interest and feasibility of using CDP interest to fund an Indigo Peg Reserve (IPR). The IPR would be a reserve of funds that could be used to exchange on the market in a fashion that helps to maintain iAsset peg.

Funding changes include
* 30% CDP interest payments going forward placed towards funding the IPR
* 30% CDP interest payments toward INDY buybacks, which are subsequently distributed to INDY stakers
* 40% CDP interest payments toward DEVOPS

## Background
#TODO

## 30% ADA on INDY Buybacks for INDY stakers
INDY buybacks have been functioning well. Since buybacks first started on X, INDY is currently up more than 50%. The Protocol Working Group (PWG) believes that this successful strategy should be continued to sustain buy pressure on the INDY token. We wish to route all INDY buybacks to INDY holders. The DAO has a surplus of INDY and, at the moment, no diversification into other assets. Furthermore,INDY stakers are seen as prime candidates to receive these INDY buybacks as data suggests that they have a 90% retention rate of their INDY rewards. INDY rewards also benefit INDY stakers as it allows their rewards to compound, i.e. INDY rewards from staking increase the holders allocation and therefore enable them to receive a larger fraction of the next round's staking rewards. 


## 30% ADA to Fund the IPR
Seeing the success of INDY buybacks, the PWG now wants to apply a similar tactic to iAssets to help them achieve and maintain peg.

## Technical Details
* IPR funds will be sent to the Indigo Labs(?) multisig and buybacks would be manual until the IPR is stood up (coded) 
* Buybacks will only ensue when the iAsset price on markets is below a buyback threshold of 97%.
* While this proposal sets the buyback threshold to 97% for all iAssets, these thresholds may be individually set per iAsset.
* IPR funds to be split for use among the available iAssets proportional to the equivalent peg value of the iAssets minted (exceptions in the case of an error in the oracle price).
* If any iAsset achieves its buyback threshold (97%) before its allotment of market buybacks is used, the remaining funds may be used towards the buybacks of other iAssets (again proportional to their relative minted value).
* If all iAssets are within their buyback threshold
