# NBA Trade & Salary Analytics Warehouse

An end-to-end NBA data engineering and analytics project that integrates player performance, team performance, salaries, salary-cap data, and historical trades into a PostgreSQL warehouse, transforms the data with dbt, and surfaces insights through an interactive Tableau dashboard.

**Tech Stack:** Python · PostgreSQL · SQL · dbt · pandas · DuckDB · Tableau · Git

## Live Dashboard

**[View the Interactive Tableau Dashboard](https://public.tableau.com/app/profile/ronit.shah2178/viz/NBATradeSalaryAnalytics/Dashboard1)**

The dashboard explores three core areas:

- **Player Value** — Which players produce the most relative to their salary?
- **Team Payroll Efficiency** — Which teams convert payroll spending into wins most efficiently?
- **Trade Acquisition Value** — Which traded players provide the strongest salary-adjusted production?

---

## Project Overview

NBA roster decisions involve more than comparing player statistics. Teams must balance performance, contracts, salary-cap constraints, team success, and the value exchanged through trades.

This project builds an analytics warehouse that brings those datasets together into a consistent analytical model.

It is designed to answer questions such as:

- Which players outperform their salary level?
- Which teams get the most wins from their payroll?
- Which trade acquisitions provide strong value relative to cost?
- How does player production compare with salary across seasons?
- How do payroll efficiency and player value differ across the league?

The pipeline takes data from raw sources through extraction, validation, transformation, warehouse modeling, dbt, and visualization.

---

## Data Coverage

| Dataset | Coverage |
|---|---:|
| Player statistics | 26 seasons |
| Team statistics | 26 seasons |
| Salary data | 17 seasons |
| Player-season records | 12,810 |
| Team-season records | 776 |
| Salary records | 9,519 |
| Historical trades | 737 |
| Trade-team relationships | 1,594 |
| Normalized trade assets | 3,432 |
| Trade-player candidates | 1,507 |
| Resolved trade-player assets | 1,491 |

Player and team performance data spans **2000-01 through 2025-26**, with historical trade data covering **2014 through September 2026**.

---

## Architecture

```text
NBA Data Sources
        |
        v
Python Extraction
        |
        v
Cleaning & Validation
        |
        v
Entity Resolution
        |
        v
PostgreSQL Warehouse
        |
        v
dbt Transformation Layer
   |-- Staging
   |-- Intermediate
   `-- Analytics Marts
        |
        v
Tableau Extracts
        |
        v
Tableau Public Dashboard
```

### Technology Stack

| Layer | Technology |
|---|---|
| Extraction | Python, pandas |
| Validation & transformation | Python, pandas |
| Analytical data access | DuckDB |
| Data warehouse | PostgreSQL |
| Analytics transformation | SQL, dbt |
| Data quality | Python validation, dbt tests |
| Visualization | Tableau Public |
| Version control | Git, GitHub |

---

## Data Pipeline

### Extraction

Python scripts collect and standardize:

- NBA player reference data
- NBA team reference data
- Player season statistics
- Team season statistics
- Historical player salaries
- Salary-cap and luxury-tax thresholds
- Historical NBA trades

Raw data is kept separate from processed warehouse-ready datasets to preserve pipeline reproducibility.

### Validation

Validation is performed before warehouse loading to identify issues such as:

- duplicate records
- missing identifiers
- schema inconsistencies
- incomplete season coverage
- salary-cap coverage gaps
- salary-to-player matching failures
- invalid trade-team mappings
- unresolved player identities

Player statistics validation:

```text
Season files: 26
Player-season rows: 12,810
Issues found: 0
```

Team statistics validation:

```text
Season files: 26
Team-season rows: 776
Issues found: 0
```

---

## Trade Processing & Entity Resolution

Historical trade data is significantly less structured than standard player and team statistics.

Individual transaction descriptions can contain:

- players
- draft picks
- draft rights
- pick swaps
- cash considerations
- trade exceptions
- alternate names
- nicknames
- suffix variations
- ambiguous historical identities

The trade pipeline parses **737 historical trades** into normalized warehouse entities:

```text
737 Trades
    |
    |-- 1,594 Trade-Team Relationships
    |
    `-- 3,432 Trade Assets
            |
            |-- Players
            |-- Draft Picks
            |-- Draft Rights
            |-- Pick Swaps
            |-- Cash
            |-- Trade Exceptions
            `-- Other Assets
```

### Player Identity Resolution

Trade-player identities are resolved using deterministic matching rather than unrestricted fuzzy matching.

The resolver uses:

1. normalized exact-name matching
2. version-controlled player aliases
3. explicit NBA player IDs for ambiguous identities
4. manual review when an identity cannot be safely inferred

Resolution results:

```text
Player candidates: 1,507
Exact matches:     1,375
Alias matches:       116
Total matched:     1,491
Unmatched:            16

Match coverage:    98.94%
Invalid aliases:        0
```

Uncertain identities are intentionally left unresolved instead of being assigned an unreliable player ID.

---

## PostgreSQL Warehouse

Processed datasets are loaded into a normalized PostgreSQL warehouse with primary keys, foreign keys, indexes, and relational constraints.

### Core Tables

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

### Core Relationships

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

The trade portion of the warehouse contains:

```text
Trades:                    737
Trade/team relationships: 1,594
Trade assets:             3,432
Player assets:            1,507
Resolved player assets:   1,491
Unresolved player assets:    16
Multi-team trades:           96
```

---

## dbt Analytics Layer

dbt provides the transformation and semantic layer between the normalized warehouse and downstream analytics.

### Staging Models

Nine staging models standardize the warehouse sources:

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

### Intermediate Model

```text
int_player_season_value
```

This model combines player performance, salary, and salary-cap information at the player-season grain.

### Analytics Marts

Three analytics marts power the final analyses and Tableau dashboard:

```text
mart_player_value
mart_team_payroll_efficiency
mart_trade_acquisition_value
```

This separation keeps warehouse storage, transformation logic, and analytical presentation independent from one another.

---

## Data Quality

Automated dbt tests validate:

- required identifiers
- non-null business fields
- uniqueness
- player relationships
- team relationships
- season relationships
- trade relationships
- analytics mart integrity

The complete dbt DAG passes end-to-end:

```text
PASS=97
WARN=0
ERROR=0
SKIP=0
TOTAL=97
```

The dbt project contains:

```text
13 models
85 data tests
9 warehouse sources
```

---

## Player Value Analytics

`mart_player_value` compares player production with salary commitments within each season.

The current production metric is intentionally simple and interpretable:

```text
Production Score =
    Points
  + Rebounds
  + Assists
  + Steals
  + Blocks
```

Players are evaluated relative to the rest of the league using salary and production percentiles:

```text
Value Gap =
    Production Percentile
  - Salary Percentile
```

A positive `Value Gap` indicates that a player's production percentile exceeds their salary percentile.

The dashboard uses this model to visualize:

- salary vs. production
- salary-adjusted value
- Top 10 player values
- season-level comparisons

---

## Team Payroll Efficiency

`mart_team_payroll_efficiency` evaluates how efficiently NBA teams convert payroll spending into regular-season wins.

Metrics include:

- total payroll
- payroll as a percentage of the salary cap
- wins and losses
- win percentage
- payroll per win
- payroll rank
- wins rank
- efficiency rank

The Tableau dashboard combines payroll and team-performance data to identify teams producing stronger results relative to their spending.

---

## Trade Acquisition Analytics

`mart_trade_acquisition_value` connects each resolved player acquisition with:

- trade
- trade date
- receiving team
- player salary
- salary-cap percentage
- season production
- salary percentile
- production percentile
- value gap

Trade acquisitions are preserved at the acquisition level rather than being aggregated only by player.

This matters when a player appears in multiple transactions during the same season: each acquisition remains a separate analytical record.

The dashboard visualizes:

- acquisition salary vs. production
- salary-adjusted acquisition value
- receiving-team context
- Top 10 trade acquisitions
- season-level trade analysis

---

## Tableau Dashboard

**[Launch the Interactive Dashboard](https://public.tableau.com/app/profile/ronit.shah2178/viz/NBATradeSalaryAnalytics/Dashboard1)**

The Tableau Public dashboard is organized into three analytical sections.

### Player Value

- NBA player salary vs. production
- Salary-adjusted value visualization
- Top 10 salary-adjusted player values
- Interactive season selection

### Team Payroll Efficiency

- Team payroll vs. wins
- Payroll efficiency visualization
- Payroll cost per win
- Top 10 payroll-efficient teams
- Interactive season selection

### Trade Analytics

- Trade acquisition salary vs. production
- Acquisition-level value analysis
- Top 10 trade acquisitions
- Receiving-team context
- Interactive season selection

The dashboard uses extracts generated from the tested dbt analytics marts.

---

## Advanced SQL

The repository includes analytical SQL using:

- multi-table joins
- common table expressions
- aggregations
- window functions
- `LAG()`
- `RANK()`
- `PERCENT_RANK()`
- `PARTITION BY`
- salary-cap normalization
- season-over-season comparisons

Example analyses include:

- player salary value rankings
- team payroll efficiency
- traded-player performance
- trade acquisition value

---

## Repository Structure

```text
NBA-Trade-Salary-Analytics-Warehouse/
|
|-- data/
|   |-- raw/
|   |-- processed/
|   |-- reference/
|   `-- tableau/
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
|       |
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

## Running the Project

### Environment

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

The warehouse uses PostgreSQL with the database:

```text
nba_analytics
```

### dbt

Navigate to the dbt project:

```bash
cd dbt/nba_analytics
```

Verify the database connection:

```bash
dbt debug
```

Build and test the complete analytics DAG:

```bash
dbt build
```

A successful build currently completes all **97 resources with zero warnings or errors**.

### Tableau Extracts

Tableau Public uses CSV extracts generated from the final dbt marts:

```bash
psql nba_analytics -c "\copy analytics.mart_player_value TO 'data/tableau/mart_player_value.csv' CSV HEADER"

psql nba_analytics -c "\copy analytics.mart_team_payroll_efficiency TO 'data/tableau/mart_team_payroll_efficiency.csv' CSV HEADER"

psql nba_analytics -c "\copy analytics.mart_trade_acquisition_value TO 'data/tableau/mart_trade_acquisition_value.csv' CSV HEADER"
```

These extracts preserve the dbt marts as the source of truth while allowing the visualization layer to be published through Tableau Public.

---

## Methodology & Limitations

### Full-Season Performance

Player performance is currently modeled at the **player-season grain**.

Trade analyses therefore use full-season statistics rather than exact pre-trade and post-trade performance splits.

A player involved in multiple transactions during one season can appear in multiple acquisition records associated with the same season-level performance.

### Player Value

The current production score emphasizes traditional box-score statistics.

It does not fully represent contributions such as:

- defensive positioning
- rim deterrence
- matchup difficulty
- defensive versatility
- off-ball impact
- screen setting
- other contributions not captured by traditional box scores

Players whose impact is heavily defensive may therefore be undervalued by the current metric.

---

## Future Improvements

Potential extensions include:

- incorporating advanced defensive-impact metrics into player valuation
- separating offensive and defensive components of player value
- adding exact pre-trade and post-trade performance splits
- expanding draft-pick and pick-swap valuation
- incorporating richer player-impact metrics
- evaluating trade outcomes across longer post-trade windows
- expanding historical trend analysis

A particularly useful extension would be incorporating defensive-impact data so that players whose value is not fully represented by traditional box-score production can be evaluated more accurately.

---

## Engineering Highlights

- Built an end-to-end analytics pipeline with **Python, PostgreSQL, SQL, dbt, and Tableau**.
- Processed **12,810 player-season records** spanning 26 NBA seasons.
- Integrated **9,519 historical salary records** with performance and salary-cap context.
- Normalized **737 historical trades** into **3,432 individual trade assets**.
- Achieved **98.94% deterministic trade-player identity resolution** without unrestricted fuzzy matching.
- Designed a normalized relational warehouse with primary keys, foreign keys, indexes, and validation constraints.
- Built staging, intermediate, and analytics layers using dbt.
- Implemented **85 automated dbt data tests**.
- Validated the complete transformation DAG with **97/97 successful resources**.
- Built and published an interactive Tableau dashboard covering player value, team payroll efficiency, and trade acquisition analytics.
