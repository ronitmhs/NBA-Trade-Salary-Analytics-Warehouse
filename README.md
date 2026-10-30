# NBA Trade & Salary Analytics Warehouse

An end-to-end NBA analytics engineering project that combines player performance, team performance, salaries, salary-cap context, and historical trades in a relational data warehouse.

The project uses **Python, PostgreSQL, SQL, dbt, and Tableau** to build a reproducible analytics pipeline for evaluating player value, team payroll efficiency, and trade acquisitions.

## Project Overview

NBA roster decisions involve more than comparing raw player statistics. Teams must balance player production, salary commitments, salary-cap constraints, team performance, and the value received through trades.

This project builds an analytics warehouse designed to answer questions such as:

- Which players provide the most production relative to their salary?
- Which teams convert payroll spending into wins most efficiently?
- Which trade acquisitions provide strong salary-adjusted production?
- How does player production change across seasons surrounding a trade?
- How have NBA salaries and salary-cap commitments changed over time?

The project currently covers:

- **26 seasons of player and team statistics from 2000-01 through 2025-26**
- **17 seasons of salary data from 2009-10 through 2025-26**
- **737 NBA trades from 2014 through September 2026**
- **5,198 players**
- **30 NBA teams**
- **12,810 player-season records**
- **776 team-season records**
- **9,519 salary records loaded into PostgreSQL**
- **3,432 normalized trade assets**

---

## Architecture

```text
NBA Data Sources
      |
      v
Python Extraction
      |
      v
Validation & Transformation
      |
      v
PostgreSQL Data Warehouse
      |
      v
dbt
  |-- Staging Models
  |-- Intermediate Models
  `-- Analytics Marts
      |
      v
Tableau
```

### Technology Stack

| Layer | Technology |
|---|---|
| Extraction | Python, pandas |
| Data validation | Python, pandas |
| External analytical data access | DuckDB |
| Warehouse | PostgreSQL |
| Transformation | SQL, dbt |
| Data quality | Python validation + dbt tests |
| Analytics | PostgreSQL SQL |
| Visualization | Tableau |
| Version control | Git, GitHub |

---

## Data Pipeline

### 1. Extraction

Python extraction scripts collect and standardize:

- NBA player reference data
- NBA team reference data
- Player season statistics
- Team season statistics
- Historical salary data
- Salary-cap and luxury-tax thresholds
- Historical trade transactions

Raw data is retained separately from processed warehouse-ready datasets.

### 2. Validation

Validation scripts check data before warehouse loading.

Examples include:

- duplicate player detection
- duplicate team detection
- expected schema validation
- salary-cap coverage
- player-ID coverage
- salary-to-player-stat join coverage
- trade-team normalization
- trade asset classification
- player identity resolution

Player statistics validation produced:

```text
Season files: 26
Player-season rows: 12,810
Issues found: 0
```

Team statistics validation produced:

```text
Season files: 26
Team-season rows: 776
Issues found: 0
```

Salary data achieved approximately **96.4% NBA player-ID coverage** before warehouse-specific reconciliation.

---

## Trade Entity Resolution

Trade data is particularly messy because transactions contain players, draft picks, pick swaps, cash, draft rights, trade exceptions, aliases, and historical naming variations.

The pipeline normalizes **737 trades** into:

```text
737 trades
 |
 |-- 1,594 trade/team relationships
 |
 `-- 3,432 trade assets
       |
       |-- player assets
       |-- draft picks
       |-- draft rights
       |-- pick swaps
       |-- cash
       |-- trade exceptions
       `-- other assets
```

Player identities are resolved using:

1. normalized exact-name matching
2. version-controlled aliases
3. explicit NBA player IDs for ambiguous historical names

The resolver intentionally avoids blind fuzzy matching.

### Resolution Results

```text
Player candidates: 1,507
Exact matches: 1,375
Alias matches: 116
Total matched: 1,491
Unmatched: 16
Match coverage: 98.94%
Invalid aliases: 0
```

Ambiguous or unverifiable identities remain unresolved rather than being assigned an unsafe player ID.

---

## PostgreSQL Warehouse

The warehouse uses normalized relational tables with primary keys, foreign keys, indexes, and validation constraints.

Core tables include:

```text
players
teams
seasons
player_season_stats
team_season_stats
player_salaries
trades
trade_teams
trade_assets
```

### Example Relationships

```text
players
   |
   +---- player_season_stats
   |
   +---- player_salaries
   |
   `---- trade_assets

teams
   |
   +---- team_season_stats
   |
   +---- player_salaries
   |
   +---- trade_teams
   |
   `---- trade_assets

seasons
   |
   +---- player_season_stats
   +---- team_season_stats
   +---- player_salaries
   `---- trades
```

Foreign-key constraints protect player, team, season, salary, and trade relationships.

---

## dbt Analytics Layer

dbt transforms the PostgreSQL warehouse into analytics-ready models.

### Staging

Nine staging models expose clean warehouse entities:

```text
stg_players
stg_teams
stg_seasons
stg_player_season_stats
stg_team_season_stats
stg_player_salaries
stg_trades
stg_trade_teams
stg_trade_assets
```

### Intermediate

Reusable business logic is separated into intermediate transformations.

Current model:

```text
int_player_season_value
```

This combines player performance and salary information at the player-season grain.

### Analytics Marts

Three core marts are currently available:

```text
mart_player_value
mart_team_payroll_efficiency
mart_trade_acquisition_value
```

These tables are designed to serve downstream BI and visualization tools.

---

## Automated Data Quality

dbt tests validate:

- primary identifiers
- required fields
- uniqueness
- player relationships
- team relationships
- season relationships
- trade relationships
- analytics mart integrity

The complete V1 dbt DAG currently passes:

```text
PASS=97
WARN=0
ERROR=0
SKIP=0
TOTAL=97
```

This includes **13 dbt models**, **85 data tests**, and **9 warehouse sources**.

---

## Analytics

### Player Value

`mart_player_value` compares player production with salary commitments within each season.

The current V1 production score is:

```text
PTS + REB + AST + STL + BLK
```

Players are ranked using salary and production percentiles.

```text
value_gap =
    production_percentile
    - salary_percentile
```

A positive value gap indicates that a player's production percentile exceeds their salary percentile.

For example, the 2025-26 analysis identifies players including Russell Westbrook, Maxime Raynaud, Toumani Camara, Collin Gillespie, and Keyonte George among the highest salary-adjusted production values in the dataset.

### Team Payroll Efficiency

`mart_team_payroll_efficiency` evaluates how efficiently teams convert payroll spending into wins.

Metrics include:

- total payroll
- payroll as a percentage of the salary cap
- wins and losses
- win percentage
- payroll per win
- payroll rank
- wins rank
- efficiency rank

For 2025-26, the model ranks Oklahoma City first in payroll-per-win efficiency, followed by San Antonio and Detroit.

### Trade Acquisition Value

`mart_trade_acquisition_value` connects:

```text
Trade
  |
  v
Receiving Team
  |
  v
Acquired Player
  |
  +-- Salary
  +-- Salary Cap %
  +-- Production
  +-- Salary Percentile
  +-- Production Percentile
  `-- Value Gap
```

This enables salary-adjusted analysis of players acquired through trades.

---

## Advanced SQL

The repository includes analytical SQL demonstrating:

- multi-table joins
- common table expressions
- aggregation
- `LAG()`
- `RANK()`
- `PERCENT_RANK()`
- `PARTITION BY`
- season-over-season comparisons
- salary-cap normalization
- payroll efficiency analysis
- trade acquisition analysis

Example analyses include:

```text
Player salary value rankings
Team payroll efficiency
Traded-player season-over-season performance
Trade acquisition value
```

---

## Repository Structure

```text
NBA-Trade-Salary-Analytics-Warehouse/
|
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- reference/
|
|-- src/
|   |-- extract/
|   |-- transform/
|   `-- load/
|
|-- sql/
|   |-- ddl/
|   `-- queries/
|
|-- dbt/
|   `-- nba_analytics/
|       |-- models/
|       |   |-- staging/
|       |   |-- intermediate/
|       |   `-- marts/
|       |
|       |-- analyses/
|       |-- macros/
|       |-- seeds/
|       |-- snapshots/
|       `-- tests/
|
|-- requirements.txt
|-- .gitignore
`-- README.md
```

---

## Running the dbt Project

From the dbt project directory:

```bash
cd dbt/nba_analytics
```

Verify the connection:

```bash
dbt debug
```

Build the complete analytics DAG:

```bash
dbt build
```

A successful V1 build currently completes all 97 resources without warnings or errors.

---

## Methodology Notes

### Full-Season Performance

Player statistics are currently stored at the **player-season grain**.

Trade analyses therefore use full-season performance and should not be interpreted as exact pre-trade versus post-trade splits.

A player traded multiple times within the same season can appear in multiple trade events associated with the same full-season performance record.

### Salary Records

Historical salary sources can contain:

- partial salary records
- players missing NBA IDs
- multiple salary records for the same player-season
- players not represented in the primary player dimension

The pipeline preserves these realities rather than silently forcing invalid joins.

### Player Value Metric

The current V1 production score is intentionally simple and transparent.

It does **not fully capture defensive impact**, off-ball value, matchup difficulty, rim deterrence, screening, or other contributions that are poorly represented by basic box-score statistics.

Players whose value is heavily defensive may therefore be underrated by V1.

---

## V2 Roadmap

Planned improvements include:

- advanced defensive impact metrics
- separate offensive and defensive value scores
- improved representation of defensive specialists
- richer player impact metrics
- exact pre/post-trade performance splits where data permits
- additional trade asset analysis
- expanded historical analytics

Examples of players motivating the defensive-impact upgrade include defensive specialists whose value is not adequately represented by basic box-score production.

---

## Tableau Dashboard

The V1 visualization layer is currently being developed in Tableau.

Planned dashboard sections include:

### Player Value

- salary vs. production
- salary percentile vs. production percentile
- value-gap rankings
- player and season filters

### Team Payroll Efficiency

- payroll vs. wins
- payroll per win
- team efficiency rankings
- historical payroll trends

### Trade Analytics

- trade acquisition value
- salary acquired
- production acquired
- salary-adjusted acquisition rankings

The Tableau layer will connect directly to the dbt analytics marts in PostgreSQL.

---

## Project Status

### Completed

- Python extraction pipeline
- historical player statistics
- historical team statistics
- salary ingestion
- salary-cap normalization
- trade ingestion
- trade normalization
- player entity resolution
- PostgreSQL warehouse
- relational constraints and indexes
- advanced SQL analytics
- dbt staging layer
- dbt intermediate transformations
- dbt analytics marts
- automated dbt testing
- successful end-to-end dbt build

### In Progress

- Tableau dashboard
- final project documentation and visualizations

### Planned V2

- defensive-impact analytics
- richer player-value methodology
- additional advanced NBA metrics

---

## Key Engineering Highlights

- Built a normalized PostgreSQL warehouse spanning player performance, team performance, salaries, salary-cap context, and trades.
- Processed **12,810 player-season records** across 26 seasons.
- Normalized **737 historical trades** into **3,432 individual trade assets**.
- Achieved **98.94% deterministic trade-player identity resolution** without blind fuzzy matching.
- Implemented dbt staging, intermediate, and mart layers.
- Added **85 automated dbt data tests** across warehouse relationships and analytics models.
- Validated the complete dbt DAG with **97/97 successful resources**.
- Developed advanced SQL analyses using CTEs and analytical window functions including `LAG()`, `RANK()`, and `PERCENT_RANK()`.

---

## Future Work

The immediate next milestone is completing the Tableau visualization layer. After V1 is finalized, the project will expand toward richer defensive-impact modeling and additional advanced player-value metrics.
