-- Double-check the datasets

SELECT * 
FROM Project_covid.dbo.[owid-covid-data_Deaths]
WHERE continent IS NOT NULL
ORDER BY 3,4

SELECT * 
FROM Project_covid.dbo.[owid-covid-data_Vaccinations]
WHERE continent IS NOT NULL
ORDER BY 3,4

 -- Calculation of the death percentage in your own country
 -- Convert nvarchar to numeric data type for calculation

SELECT Location, date, total_cases, total_deaths, CONVERT(float, total_deaths) / CONVERT(float, total_cases) * 100 AS Death_percentage
FROM Project_covid.dbo.[owid-covid-data_Deaths]
WHERE Location like '%China'AND continent IS NOT NULL
ORDER BY 1,2

-- Calculation of the percentage of population infected with covid-19

SELECT Location, date, population, total_cases, CONVERT(float, total_deaths) / CONVERT(float, total_cases) * 100 AS Death_percentage
FROM Project_covid.dbo.[owid-covid-data_Deaths]
WHERE continent IS NOT NULL
ORDER BY 1,2

-- Caluculation of the highest infection rate compared to population of countries
-- The proportion of the population that has been affected by covid-19 = total case / population
-- The highest proportion of the population that has been affected by covid-19 = max of (total case / population)

SELECT location,population, MAX(CONVERT(int,total_cases)) AS highest_infection, MAX(CONVERT(int, total_cases) / population) * 100 AS prop_population_infected
FROM Project_covid.dbo.[owid-covid-data_Deaths]
WHERE continent IS NOT NULL
GROUP BY location, population
ORDER BY prop_population_infected DESC

-- Caluculation of the highest death rate compared to population of countries

SELECT location,MAX(CONVERT(int,total_deaths)) AS highest_death, MAX(CONVERT(int, total_deaths) / population)* 100 AS total_death_rate
FROM Project_covid.dbo.[owid-covid-data_Deaths]
WHERE continent IS NOT NULL
GROUP BY location
ORDER BY highest_death DESC

-- Break things down by continents with the highest death count per population

SELECT continent, MAX(CONVERT(int,total_deaths)) AS highest_death, MAX(CONVERT(int, total_deaths) / population)* 100 AS total_death_rate
FROM Project_covid.dbo.[owid-covid-data_Deaths]
WHERE continent IS NOT NULL
GROUP BY continent
ORDER BY highest_death DESC

-- Total cases across the world
SELECT SUM(new_cases) AS total_cases, SUM(new_deaths) AS total_deaths, SUM(new_deaths)/SUM(new_cases) * 100 AS deathpercentage
FROM Project_covid.dbo.[owid-covid-data_Deaths]
ORDER BY 1,2

-- Caluculation of the percentage of population that has recieved at least one covid vaccine

--- Merge two files
---  Convert the data type to bigint since the value is too large for the data type (int) of the column
--- Use CTE to solve the error that using the '#_people_vaccinated column' that just created for calculation
WITH pop_vs_Vaccine (continent, location, population, #_people_vaccinated)
AS
(
SELECT deaths.continent, deaths.location,deaths.population, MAX(CONVERT(bigint,vacc.people_vaccinated)) AS #_people_vaccinated
FROM Project_covid.dbo.[owid-covid-data_Deaths] deaths
JOIN Project_covid..[owid-covid-data_Vaccinations] vacc
ON deaths.location = vacc.location
AND deaths.date = vacc.date
WHERE deaths.continent IS NOT NULL AND vacc.people_vaccinated IS NOT NULL
GROUP BY deaths.continent,deaths.location,deaths.population
)
SELECT *, (#_people_vaccinated/population)*100 AS percentage_vaccinated
FROM pop_vs_Vaccine

-- Create View to store data for later data visualizations
CREATE VIEW PercentPopulationVaccinated AS
SELECT deaths.continent, deaths.location,deaths.population, MAX(CONVERT(bigint,vacc.people_vaccinated)) AS #_people_vaccinated
FROM Project_covid.dbo.[owid-covid-data_Deaths] deaths
JOIN Project_covid..[owid-covid-data_Vaccinations] vacc
ON deaths.location = vacc.location
AND deaths.date = vacc.date
WHERE deaths.continent IS NOT NULL AND vacc.people_vaccinated IS NOT NULL
GROUP BY deaths.continent,deaths.location,deaths.population

-- Double check the view
SELECT * 
FROM PercentPopulationVaccinated 
