# Civic Opportunity Dashboard


## Project Structure

The project consists of the following key files and directories:

### 1. **`_quarto.yml`**
- This file contains the configuration settings for the Quarto project.
- It defines the **website structure** and page links, as well as specifying the format and theme for rendering the dashboard.
- It also includes metadata like the project type and navbar setup for navigation.

### 2. **`index.qmd`**
- The **landing page** for the dashboard.
- This file introduces the project, explains the **motivation** behind the dashboard, and provides context on how **civic opportunities** are distributed across the U.S.
- It includes a summary of the **dataset construction** and **methodology** used to collect data on civic engagement.
- The page also includes navigation links to the other sections of the dashboard.

### 3. **`map.qmd`**
- This file contains the code to generate **the interactive map** that visualizes the civic opportunity data.
- It uses the **`leaflet`** package to create an interactive map that displays civic opportunities at the **county level**.

### 4. **`table.qmd`**
- This file contains the code to generate **the interactive table** that filters and sorts the civic opportunity data.
- It uses the **`DT`** package to display the table, which allows users to **filter and sort** the data.

### 5. **`raw_data/`**
- This directory contains the raw data files used in the project.
- **`cnty_counts_cov.csv`**: A CSV file that contains data on various civic organizations, including their **FIPS code**, **civic opportunity measures**, and **other relevant attributes**.
- **`counties.rds`** and **`states.rds`**: RDS files that contain shapefiles for U.S. counties and states, which are used to plot the map and ensure geographic accuracy.

### 6. **`deploy_dashboard.sh`**
- A **Bash script** that automates the process of **rendering** the Quarto site, **copying the files** to the `docs/` folder, and **pushing the changes** to GitHub.
- It simplifies the process of updating the live dashboard on **GitHub Pages** by handling the full deployment pipeline in one command.
