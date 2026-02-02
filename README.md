---
title: "README"
format: html
---

# MapAgora Teaching Dashboard

![Version](https://img.shields.io/badge/version-beta-blue)

An interactive teaching tool for exploring civic opportunities across U.S. counties, built from the MapAgora datasets developed at the [SNF Agora Institute](https://snfagora.jhu.edu/), Johns Hopkins University.

Developed and maintained by:
[Jae Yeon Kim](https://jaeyk.github.io/) & [Milan de Vries](https://snfagora.jhu.edu/person/milan-de-vries/)

---

## Overview

This dashboard provides an interactive interface for **learning about and exploring** the county-level landscape of civic opportunity in the United States. It draws from the *Mapping the Modern Agora (MMA)* project, which combines IRS administrative records and scraped web data to construct a scalable measure of civic infrastructure.

### Teaching Tool Features

- **Learn**: Comprehensive methodology explanation covering data sources, collection methods, and limitations
- **Guided Exploration**: Step-by-step instructions for exploring the map and table
- **Interactive Map**: County-level visualization with annotation and comparison tools
- **Interactive Table**: Searchable data with bookmarking functionality
- **Compare**: Side-by-side state and county comparisons

---

## Quick Links

- [**Learn the Methodology**](https://snfagora.github.io/agora_dashboard/learn.html)
- [**Where to Start**](https://snfagora.github.io/agora_dashboard/where_to_start.html)
- [**Interactive Map**](https://snfagora.github.io/agora_dashboard/map.html)
- [**Interactive Table**](https://snfagora.github.io/agora_dashboard/table.html)
- [**Compare Counties**](https://snfagora.github.io/agora_dashboard/compare.html)

---

## Project Structure

### Core Pages

| File | Description |
|------|-------------|
| `index.qmd` | Landing page with project overview and data access |
| `learn.qmd` | Comprehensive methodology (data sources, collection, limitations) |
| `where_to_start.qmd` | Learning objectives and guided exploration steps |
| `map.qmd` | Interactive Leaflet map with annotations and comparison mode |
| `table.qmd` | Interactive DataTable with bookmark functionality |
| `compare.qmd` | State and county comparison tools |
| `about.qmd` | Credits and contact information |

### Configuration

| File | Description |
|------|-------------|
| `_quarto.yml` | Site configuration and navigation |
| `style.css` | Custom styles for teaching features |
| `deploy_dashboard.sh` | Deployment script for GitHub Pages |

### Data

| File | Description |
|------|-------------|
| `raw_data/cnty_counts_cov.csv` | County-level civic indicators |
| `raw_data/cnty_civic_org_type.csv` | Organizational type frequencies |
| `raw_data/counties.rds` | County shapefiles |
| `raw_data/states.rds` | State shapefiles |
| `misc/Kim_et_al-2025-Scientific_Data.pdf` | Source methodology paper |

---

## Key Features

### Map Features
- **Click any county** to see detailed civic opportunity metrics
- **Annotation panel**: Add personal notes to counties (saved in browser)
- **Comparison mode**: Select up to 3 counties for side-by-side comparison
- **Layer toggle**: Switch between civic opportunity index and organization type views
- **Search**: Find counties by name

### Table Features
- **Bookmark counties**: Click star icons to save counties of interest
- **Filter bookmarks**: Show only your bookmarked counties
- **Export**: Download visible data as CSV
- **Sort & filter**: Click headers and use column filters

### Compare Page
- **State comparison**: View all states ranked by civic opportunity
- **County comparison**: Filter by state, compare specific counties
- **Quick compare**: Side-by-side metric cards for two counties

---

## Data Access

This dashboard uses **county-level aggregates** from the full MapAgora data:

| Dataset | Description | Included? |
|---------|-------------|-----------|
| Dataset 1 | 1.7M+ de-identified nonprofit organizations | No |
| Dataset 2 | County-level civic opportunity counts | **Yes** |
| Dataset 3 | ZIP code-level civic opportunity counts | No |
| Dataset 4 | County-level organizational type breakdowns | **Yes** |
| Dataset 5 | ZIP code-level organizational type breakdowns | No |

**Full Data Access**:
- [GitHub Repository](https://github.com/snfagora/american_civic_opportunity_datasets)
- [Harvard Dataverse](https://doi.org/10.7910/DVN/IRCA7C)

---

## References

- **Data paper**: Kim, J.Y., de Vries, M., & Han, H. (2025). ["MapAgora, Civic Opportunity Datasets for the Study of American Local Politics and Public Policy."](https://www.nature.com/articles/s41597-025-05353-6) *Nature: Scientific Data*.

- **Empirical paper**: de Vries, M., Kim, J.Y., & Han, H. (2023). ["The Unequal Landscape of Civic Opportunity in America."](https://www.nature.com/articles/s41562-023-01743-1) *Nature Human Behaviour*.

- **Concept paper**: Han, H. & Kim, J.Y. (2022). ["Civil Society, Realized."](https://journals.sagepub.com/doi/full/10.1177/00027162221077471) *The ANNALS of the American Academy of Political and Social Science*.

---

## Development

```bash
# Preview locally
quarto preview

# Render the site
quarto render

# Deploy to GitHub Pages
bash deploy_dashboard.sh
```

---

## Contributing & Feedback

This is a **beta release**. We welcome suggestions and contributions.

Contact: [Jae Yeon Kim](https://jaeyk.github.io/)
