# Global Signal Dashboard Trading Guide

## What This Project Is

This project is a notebook-based trading decision system built around market regime, breadth, constituent leadership, and trade construction.

It is not a single indicator and it is not a black-box "buy/sell" model.

Instead, it combines:

- index trend and volatility context
- breadth and participation
- constituent-level opportunity ranking
- sector leadership and concentration checks
- scenario planning
- execution and risk budgeting

The goal is to help answer five trading questions:

1. What is the market environment right now?
2. What kinds of trades fit that environment?
3. Which index or stock ideas are strongest?
4. How should those ideas be sized and expressed?
5. What would invalidate the current plan?

## What The Dashboard Produces

The dashboard is designed to move from top-down context to bottom-up trade expression.

At a high level, the output falls into six layers.

### 1. Market Regime

This tells you whether the market is acting risk-on, mixed, or risk-off.

Main outputs:

- `Executive Summary`
- `Regime Radar`
- `Scenario Deck`
- `Signal Drift`

How to use it:

- If the regime is bullish and improving, favor continuation and pullback longs.
- If the regime is mixed, trade smaller and be more selective.
- If the regime is deteriorating or bearish, reduce gross exposure, use more hedges, and demand stronger setup quality.

### 2. Trade Opportunity Discovery

This is where the notebook surfaces actual setups.

Main outputs:

- `Trade Ideas`
- `Constituent Ideas`
- `Action Board`
- `Catalyst Grid`

How to use it:

- `Trade Ideas` gives the main index-level expressions.
- `Constituent Ideas` shows the raw stock-level opportunity set.
- `Action Board` is the cleaner, diversification-aware shortlist.
- `Catalyst Grid` explains why ideas exist now: trend continuation, trend repair, mean reversion, momentum continuation, or hedge/protection.

### 3. Leadership And Participation

This checks whether market strength is broad and healthy or narrow and fragile.

Main outputs:

- `Breadth`
- `RRG`
- `Leadership Map`

How to use it:

- Healthy breadth and broad leadership support taking more risk.
- Narrow leadership means the index may still rise, but the opportunity set is more fragile.
- If only a few sectors are working, avoid treating that as a fully healthy bull regime.

### 4. Execution Layer

This is where ideas become tradable plans.

Main outputs:

- `Entry Planner`
- `Execution`
- `Sizing`

How to use it:

- `Entry Planner` gives trigger, pullback, and failure levels.
- `Execution` summarizes what to do now, not just what looks good.
- `Sizing` translates conviction and risk distance into smaller or larger starter expressions.

### 5. Portfolio Construction

This helps turn separate ideas into a coherent book.

Main outputs:

- `Trade Book`
- `Risk Budget`
- `Concentration Risk`

How to use it:

- `Trade Book` proposes a portfolio structure from the best current ideas.
- `Risk Budget` tells you what gross, net, hedge, and cash posture fits the current regime.
- `Concentration Risk` warns when too much of the book depends on one side, one sector cluster, or too little cash.

### 6. Risk Control

This is the defensive layer.

Main outputs:

- `Tripwires`
- `Risk`
- `Outlook`

How to use it:

- `Tripwires` defines the conditions that would weaken or break the current view.
- `Risk` shows volatility and stress-related context.
- `Outlook` lets you compare current conditions with historical forward behavior.

## Recommended Trading Workflow

This is the intended order of use.

### Step 1: Start With The Regime

Open:

- `Executive Summary`
- `Regime Radar`
- `Scenario Deck`
- `Signal Drift`

Ask:

- Is the environment bullish, tactical, or defensive?
- Are conditions improving or deteriorating?
- Is the highest-probability path continuation, chop, or breakdown?

Do not start from stock picking before this step.

### Step 2: Look For The Right Type Of Trade

Open:

- `Trade Ideas`
- `Catalyst Grid`

Ask:

- Is the notebook favoring trend continuation, repair, mean reversion, or hedging?
- Does that match the regime?

Example:

- In a weak or mixed regime, defensive hedges and selective long repairs make more sense than aggressive breakout chasing.

### Step 3: Narrow To Actionable Names

Open:

- `Constituent Ideas`
- `Action Board`
- `Leadership Map`

Ask:

- Which names are strongest after diversification?
- Which sectors are actually leading?
- Are the names aligned with the healthiest leadership groups?

Use the `Action Board` more than the raw constituent list when actually building trades.

### Step 4: Build The Trade

Open:

- `Entry Planner`
- `Execution`
- `Sizing`

Ask:

- Where do I enter?
- Do I want breakout entry, pullback entry, or a smaller probe?
- How aggressive should I be?

This is where the notebook becomes practical:

- entry level
- stop or failure level
- target
- size expression

### Step 5: Build The Book

Open:

- `Trade Book`
- `Risk Budget`
- `Concentration Risk`

Ask:

- Does the portfolio fit the regime?
- Is the current book too long, too short, too concentrated, or too fully invested?
- Should I raise cash, add hedges, or spread exposure across more sectors?

### Step 6: Define What Would Make You Wrong

Open:

- `Tripwires`

Ask:

- Which conditions are already broken?
- Which are close to breaking?
- What is the response if that happens?

This step is critical. The dashboard is strongest when it is used not only to find trades, but to define when to stop believing them.

## How To Read The Most Important Tabs

## Executive Summary

Use this as the top-down snapshot.

It tells you:

- market bias
- tape condition
- participation quality
- best current setup

Best use:

- first stop when changing markets

## Trade Ideas

This is the main index setup board.

It ranks index-level trades by:

- signal alignment
- historical edge
- sample support
- reward-to-risk

Best use:

- choose the market expression that best fits current regime

## Constituent Ideas

This is the broader stock-level opportunity list.

Best use:

- explore the full opportunity set before narrowing down

## Action Board

This is the better shortlist for actual trading because it applies diversification logic.

Best use:

- pick candidate names without overloading one sector or one theme

## Catalyst Grid

This shows what kind of market behavior is producing ideas.

Best use:

- understand whether the notebook is seeing continuation, repair, reversion, or defense

## Leadership Map

This tells you which sectors are carrying the opportunity set.

Best use:

- favor names in leading sectors
- be cautious when leadership is narrow

## Playbook

This is the tactical summary.

Best use:

- quick answer to "what matters most right now?"

## Tripwires

This is one of the most important tabs.

Best use:

- define invalidation
- stop guessing when a view is no longer valid

## Concentration Risk

This protects against building a portfolio that looks diversified on paper but is really one macro bet.

Best use:

- check sector concentration
- check directional skew
- check cash discipline

## Regime Radar

This translates signals into bull/base/bear odds.

Best use:

- determine posture, not specific entries

## Scenario Deck

This tells you what to do if the market continues, chops, or breaks down.

Best use:

- pre-plan reactions instead of improvising after the move

## Entry Planner

This converts ideas into levels.

Best use:

- execution planning

## Execution

This is the action checklist.

Best use:

- quick review before placing or managing trades

## Risk Budget

This converts the dashboard state into exposure targets.

Best use:

- align gross, net, hedge sleeve, and cash with the current environment

## Sizing

This tells you how aggressive the initial expression should be.

Best use:

- avoid full-size entries in weak or fragile conditions

## Trade Book

This is the notebook's suggested portfolio expression of current opportunities.

Best use:

- turn the dashboard into an actual tradable book structure

## How To Use It For Different Trading Styles

### Swing Trading

Most useful tabs:

- `Regime Radar`
- `Trade Ideas`
- `Action Board`
- `Entry Planner`
- `Tripwires`

Use case:

- hold trades for days to weeks
- use pullbacks and trend repair setups
- size from the `Sizing` and `Risk Budget` tabs

### Tactical Macro / Index Trading

Most useful tabs:

- `Executive Summary`
- `Trade Ideas`
- `Scenario Deck`
- `Tripwires`
- `Risk Budget`

Use case:

- express views through index exposures and hedges
- let constituent information confirm or question the index view

### Long/Short Portfolio Construction

Most useful tabs:

- `Action Board`
- `Leadership Map`
- `Trade Book`
- `Concentration Risk`
- `Risk Budget`

Use case:

- build a more balanced book
- avoid unintended sector crowding
- keep the long/short mix matched to regime

## What Good Use Looks Like

Good use of the dashboard looks like this:

1. Read the regime.
2. Choose the trade style that fits the regime.
3. Use the diversified shortlist, not just the raw highest scores.
4. Plan entries before putting risk on.
5. Size smaller when tripwires or concentration warnings are elevated.
6. Re-check the dashboard when the market changes materially.

## What Bad Use Looks Like

Poor use of the dashboard looks like this:

- using only one tab in isolation
- treating high conviction as certainty
- ignoring tripwires
- ignoring concentration warnings
- forcing aggressive long books in mixed or deteriorating conditions
- trading every idea instead of choosing the best-aligned ones

## Practical Guardrails

- The dashboard is a decision support tool, not a guarantee engine.
- Strong ideas still need risk control.
- A high-conviction setup in a weak regime should usually be sized smaller than the same setup in a healthy regime.
- Narrow leadership deserves caution.
- If tripwires are stacking up, defense matters more than finding another long.
- If the risk budget is calling for more cash, listen to it.

## Best Way To Use The Project Day To Day

For a daily workflow:

1. Open the notebook and refresh the market you care about.
2. Read `Executive Summary`, `Regime Radar`, and `Scenario Deck`.
3. Check `Tripwires` and `Concentration Risk`.
4. Review `Trade Ideas`, `Action Board`, and `Catalyst Grid`.
5. Use `Entry Planner`, `Execution`, and `Sizing` to decide actual entries.
6. Use `Trade Book` and `Risk Budget` to align the overall portfolio.

## Final Framing

This project is best understood as a trading operating system.

It does not just try to answer "what should I buy?"

It tries to answer:

- what environment am I trading in?
- what kind of trade fits that environment?
- which specific ideas are worth attention?
- how should I enter them?
- how should I size them?
- how should the whole book be balanced?
- what would tell me I am wrong?

That is the real value of the project.
