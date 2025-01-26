# Proposal to Enact a New Type of Stability Pool

This proposal is to create and enact a new type of stability pool to handle Indigo iAsset liquidations. The new pool structure draws upon many of the existing features of the current stability pool, but enhances them to address peg stability as well. As such, these will be referred to as "Stability Pools Version 2" (SPv2). ~~Additionally, the Indigo DAO is preparing to add additional verified collateral assets (VCA) and so the following proposal also makes suggestions for integrating these VCA into stability pools as well.~~


## Acronyms
CDP - Collateralized Debt Position\
CR - Collateralization Ratio\
DAO - Decentralized Autonomous Organization\
DEX - Decentralize Exchange\
IPR - Indigo Peg Reserve\
MCR - Minimum Collateralization Ratio\
OPEX - Operational Expenses\
PWG - Protocol Working Group\
UI - User Interface\
SP - Stability Pool
SPv2 - Stability Pool Version 2\
VCA - Verified Collateral Asset (asset accepted as collateral backing for iAsset, currently ADA)

## Background
The [Indigo Protocol v2.1](https://app.indigoprotocol.io/governance/polls/63) upgrade introduced algorithmic interest rates for CDPs. Despite this advancement, it proved difficult for iAssets to maintain their peg price on the open market until the introduction of various stable-swap pools on DEX. This depeg was primarily due to the reliance on incentives or disincentives to gradually steer the market price (such as interest rates) rather than a "hard" peg mechanism (such as redemptions) to maintain price. While the protocol does have a redemption mechanism, it is still "voluntary" in the sense that CDP owners may optionally provide collateral beyond the minimum collateralization ratio (MCR) to prevent themselves from being redeemed against. The stableswap pools effectively act like a hard peg mechanism as, with sufficient depth, it enables users to exchange iAssets (for another asset which is backed by the underlying asset) near a 1:1 ratio at any time.

## Stability Pool Version 2
A user interface (UI) will be stood up by Indigo Labs on https://app.indigoprotocol.io/ for users to interact with the SPv2. These SP will act similar to a stableswap on DEX and typically users deposit both an iAsset along with another asset (either native, or bridged) that is backed by the asset that serves as the iAsset's peg. For example, users depositing into the iUSD SPv2 would deposit both iUSD and bridged USDC (or USDM). The ratio of assets deposited would not necessarily need to be at a 1:1, but would give them proportional ownership of the pool depending on the relative value of their deposit to the TVL in the pool. Withdrawals from the SPv2 would return the user their relative proportion of the pool the current ratio of the assets within the pool.

Example:
The current SPv2 has 100 iUSD and 100 USDC. A user deposits 20 iUSD and 10 USDC into the pool and so the new pool allocations are 120 iUSD and 110 USDC. The user now owns approximately 12.88% of the pool. If the user wished to immediately withdraw their fraction from the pool they would receive 15.4545 iUSD and 14.1667 USDC, less any withdrawal fees.

At most times, the SPv2 acts just as any other stableswap on a DEX. However, when it comes times for liquidations to occur, a withdrawal of assets is made from the pool. The amount withdrawn is equal to the amount of the iAsset that needs to be liquidated along with the other paired asset at an equal ratio to what the current pools makeup is. As an example, if this SPv2 consists of iUSD-USDC with 120 iUSD and 110 USDC and 20 iUSD is set to be liquidated, then 20 iUSD and 18.333 USDC is withdrawn from the SPv2. Subsequently, the 20 iUSD is liquidated and the over-collateralize VCA backing that liquidated iUSD along with the 18.333 USDC are distributed proportionally to the SPv2 stakers.

## Pros and Cons
### Pros
* Stability Pool has a utility 24/7 vs only during liquidations
* Stability Pool actually helps to maintain peg stability as well
### Cons
* Only works for assets that have a backed variant on chain (such as bridged BTC, ETH, SOL, USD, etc.)
* Exposes the SP to risks associated with bridge hacks, etc.
* Contention issues withdrawing from the pool during liquidations?
* Exacerbates issues with dust collection, minUTXO, etc. from more assets?
* Withdrawal fee would have to be high enough to avoid whales making "cheaper trades" by depositing/withdrawing from SPv2 vs a DEX exchange (need to test if this is actually exploitable)?

## New Parameters
Each new SP will have a set of parameters
* an "alpha" parameter, determining how the pool price varies with different ratios of assets
* a withdrawal fee for stability pool stakers withdrawing their funds