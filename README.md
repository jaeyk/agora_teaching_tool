---
title: "README"
format: html
---

# 🗺️ MapAgora Dashboard

![Version](https://img.shields.io/badge/version-beta-blue)

An interactive visualization of civic opportunities across U.S. counties, built from the MapAgora datasets developed at the [SNF Agora Institute](https://snfagora.jhu.edu/), Johns Hopkins University.

Developed and maintained by:  
[Jae Yeon Kim](https://jaeyk.github.io/) & [Milan de Vries](https://snfagora.jhu.edu/person/milan-de-vries/)

---

## 🚀 Overview

This dashboard provides an interactive interface for exploring the **county-level landscape of civic opportunity** in the United States. It draws from a larger project, *Mapping the Modern Agora (MMA)*, which combines IRS administrative records and scraped web data to construct a scalable measure of civic infrastructure.

The dashboard includes:

- A **leaflet-based map** of civic opportunity indicators  
- An **interactive data table** for filtering and comparing counties  

📍 This version only includes **county-level aggregates**. For ZIP code–level data and the full organization-level dataset, see the links below.

---

## 🧱 Project Structure

### `index.qmd`  
Landing page. Includes project background, dataset construction, and links to visualizations and data.

### `map.qmd`  
Interactive county-level map using `leaflet`. Visualizes civic opportunity index and organization types.

### `table.qmd`  
Interactive data table using `DT`. Enables filtering, sorting, and exporting of civic opportunity indicators.

### `_quarto.yml`  
Site configuration and navigation setup for the Quarto project.

### `raw_data/`  
Raw inputs for map and table generation:  
- `cnty_counts_cov.csv`: County-level civic indicators  
- `cnty_civic_org_type.csv`: Organizational type frequencies  
- `counties.rds` / `states.rds`: Shapefiles for geographic visualization

### `deploy_dashboard.sh`  
Bash script to render the site and deploy to GitHub Pages (`docs/` folder).

---

## 🌐 Access the Dashboard

- 🗺️ [**Interactive Map**](https://snfagora.github.io/agora_dashboard/map.html)  
- 📋 [**Interactive Table**](https://snfagora.github.io/agora_dashboard/table.html)

---

## 📂 Data Access

This dashboard uses **only a subset** of the full MapAgora data:

| Dataset | Description |
|--------|-------------|
| Dataset 1 | 1.3M+ de-identified nonprofit organizations (organization-level) ❌ *not included here* |
| Dataset 2 | ZIP and county-level civic opportunity counts ✅ *(only county shown)* |
| Dataset 3 | ZIP and county-level organizational type breakdowns ✅ *(only county shown)* |

- 🔗 [GitHub Repository](https://github.com/snfagora/american_civic_opportunity_datasets)  

- 🗃️ [Harvard Dataverse](https://doi.org/10.7910/DVN/IRCA7C)  

- 📄 **Data paper**:  
  ["The Mapping the Modern Agora Data Paper: MapAgora, Civic Opportunity Datasets for the Study of American Local Politics and Public Policy"](https://www.nature.com/articles/s41597-025-05353-6.epdf?sharing_token=4HNrMMO7VOt9eQU42u5HrtRgN0jAjWel9jnR3ZoTv0Mpc6G86FwIcTyoYmFsd3Uahts-NrsxWU-Q0gVeUk6vtZN_k8pGamsuixpoqi1fOhudhtavd6jX7U8p5I4FQf1oJKpcfff8nLXFvlsgow1agfORM7KYSpMi13jgivdJVAs%3D) — *Nature: Scientific Data*, 2025  
  *(Jae Yeon Kim, Milan de Vries, & Hahrie Han)*  
  [Replication](https://github.com/snfagora/american_civic_opportunity_datasets) • [Supplement](https://www.readcube.com/articles/supplement?doi=10.1038%2Fs41597-025-05353-6&index=0)

---

## 📚 References

- **Concept paper**:  
  ["Civil Society, Realized"](https://journals.sagepub.com/doi/full/10.1177/00027162221077471) — *The ANNALS of the American Academy of Political and Social Science*, 2022  
  *(Hahrie Han & Jae Yeon Kim)*

- **Empirical paper**:  
  ["The Unequal Landscape of Civic Opportunity in America"](https://www.nature.com/articles/s41562-023-01743-1) — *Nature Human Behaviour*, 2023  
  *(Milan de Vries, Jae Yeon Kim, & Hahrie Han)*  
  [Replication](https://github.com/snfagora/map_civic_opportunity/tree/main) • [Supplement](https://static-content.springer.com/esm/art%3A10.1038%2Fs41562-023-01743-1/MediaObjects/41562_2023_1743_MOESM1_ESM.pdf)

---

## 💡 Contributing & Feedback

This is a **beta release**. We welcome suggestions and contributions.

➡️ Contact: [Jae Yeon Kim](https://jaeyk.github.io/)
