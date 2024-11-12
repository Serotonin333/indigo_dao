# Proposal to Enact an Indigo Peg Reserve

This proposal is to restructure the Indigo Protocol's interest from collateralized debt positions (CDPs) to fund and enact an Indigo Peg Reserve (IPR). The IPR is a reserve of funds that market participants can interact with via the Indigo Protocol app for the exchange of assets in a fashion that helps to maintain iAsset peg.

Funding changes include
* 30% CDP interest payments going forward placed towards funding the IPR
* 30% CDP interest payments toward INDY buybacks, which are subsequently distributed to INDY stakers

## Acronyms
CDP - Collateralized Debt Position\
CR - Collateralization Ratio\
DAO - Decentralized Autonomous Organization\
IPR - Indigo Peg Reserve\
MCR - Minimum Collateralization Ratio\
OPEX - Operational Expenses\
PWG - Protocol Working Group\
UI - User Interface\
VCA - Verified Collateral Asset (asset accepted as collateral backing for iAsset, currently ADA)

## Background
The [Indigo Protocol v2.1](https://app.indigoprotocol.io/governance/polls/63) upgrade introduced algorithmic interest rates for CDPs. Despite this advancement, it has proven difficult for iAssets to maintain their peg price on the open market. This is primarily due to the reliance on incentives or disincentives to gradually steer the market price (such as interest rates) rather than a "hard" peg mechanism (such as redemptions) to maintain price. While the protocol does have a redemption mechanism, it is still "voluntary" in the sense that CDP owners may optionally provide collateral beyond the minimum collateralization ratio (MCR) to prevent themselves from being redeemed against.

As such, an additional "hard" mechanism must be introduced if iAssets are expected to maintain their peg valuation on open markets. This mechanism, ideally, would remain in effect all of the time (unlike redemptions, which are limited to instances in which there are CDPs within the redemption zone). This proposal supports the creation and funding of an IPR to provide immediate buy/sell pressure on the market, as needed to maintain iAsset peg. Of course, its effectiveness is limited to the resources available to it, but over time as the IPR grows, it will become more capable of abosorbing short term market fluctuations that would cause deviations in iAsset price from their pegged value.

## 30% ADA on INDY Buybacks for INDY stakers
INDY buybacks have been functioning well. Since buybacks first started on August 19, 2024, INDY is currently up more than 200% vs ADA (which is up 70% vs USD itself). The Protocol Working Group (PWG) believes that this successful strategy should be continued to sustain buy pressure on the INDY token. We wish to route all INDY buybacks to INDY holders. The DAO has a surplus of INDY and, at the moment, no diversification into other assets. Furthermore, INDY stakers are seen as prime candidates to receive these INDY buybacks as data suggests that they have a 90% retention rate of their INDY rewards. INDY rewards also benefit INDY stakers as it allows their rewards to compound, i.e. INDY rewards from staking increase the holders allocation and therefore enable them to receive a larger fraction of the next round's staking rewards. 


## 30% ADA to Fund an IPR
Seeing the success of INDY buybacks, the PWG now wants to apply a similar tactic to iAssets to help them achieve and maintain peg. By funding an IPR with 30% CDP interest revenue, the DAO will be providing resources to directly help stabilize and maintain iAsset values near their peg price. As funding is be dependent on the amount of CDP interest generated, the availability of tradeable assets (or assets for buybacks) will be self-limiting depending on the success of the protocol. More demand for CDPs and interest generated builds a larger reserve of assets to help stabilize iAsset peg, furthering user confidence that iAssets will retain their pegged value on the market.

## The IPR
A user interface (UI) will be stood up by Indigo Labs on https://app.indigoprotocol.io/ for users to interact with the IPR so they may exchange iAssets for ADA or other verified collateral asset (VCA) similar to a liquidity pool. iAssets will be available for exchange with a VCA at the iAsset peg price, less a fee. All fees are initially set to 3%. For users interacting with the IPR, it effectively means that they will be able to sell iAssets to the IPR at 97% their peg price and purchase them from the IPR at 103% their peg price. From a peg perspective, this means that the market price for iAssets should remain within 3% of their peg price, provided sufficient assets are available within the IPR. Lowering these fees allows the DAO to maintain a tighter peg on iAssets, but also increases the risk of the IPR becoming one-sided more quickly and losing its ability to maintain peg.

Importantly, the IPR, and all assets held within it, remain DAO owned assets. As such, the IPR can be seen as an extension of the DAO Treasury and are its funds are available for redistribution at any time via a successful proposal and vote.

While the UI and automation of the IPR is being stood up, IPR funding will be sent to the Indigo Foundation multisig script to be utilized for manual buybacks of iAssets if their market price moves below 97% of their peg.

## Technical Details
* IPR funds will be sent to the Indigo Labs multisig and buybacks will be manual until the IPR is stood up (coded) 
* Buybacks will only ensue if the iAsset price on markets is below a buyback threshold of 97% peg price (price after fee)
* While this proposal sets the buyback threshold to 97% for all iAssets, these thresholds may be individually set per iAsset.
* IPR funds will be distributed into separate pools for each iAsset, according to their relative time averaged total value locked (TVL) over the period since the last distribution. An exception will be made in the event of an error in the oracle price.
* Assets within each IPR pool are decoupled to prevent the market effects of one iAsset from affecting availability of IPR funds for other iAssets. A DAO vote is required to move funds from one iAsset IPR pool to another.
* Signatures from either the PWG multisig or the Indigo Foundation multisig may halt exchanges with the IPR as a failsafe in catastrophic situations.

## New Parameters
A pair of new parameters will be added for each iAsset pool that the DAO may vote on. Initially these values are set to 3% for all iAssets
* IPR iAsset Exchange Fee (3%) - fee a user pays to sell iAssets to the IPR
* IPR VCA Exchange Fee (3%) - fee a user pays to purchase iAssets to the IPR (sell VCA to the IPR)

## Parameter Changes
The currently enacted [Proposal #53: Phase One Treasury Management](https://app.indigoprotocol.io/governance/polls/53)  allocates

* 40% Operational Expenses (OPEX)
* 30% distributed pro rata to INDY stakers
* 30% INDY buybacks sent to the DAO Treasury

and would be revised with the following allocations

* 40% Operational Expenses (OPEX) - no change
* 30% INDY buybacks distributed pro rata to INDY stakers
* 30% IPR funding