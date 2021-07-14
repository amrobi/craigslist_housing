library(sf)      # For shapefile compatibility
library(rgdal)   # For CRS projection
library(dplyr)   # Data wrangling etc.
library(ggplot2) # Plotting
library(readr)   # Read in csv
library(tidyr)   # Unnest
source("neighborhood_functions.R")
# Load in neighborhood boundary data, convert from US Census to lat/long
neighborhoods <- 
  sf::st_read('maps/Neighborhoods_2012b.shp') %>% 
  st_transform(CRS('+proj=longlat'))

census_tracts <- 
  sf::st_read('maps/census_tracts.shp') %>% 
  st_transform(CRS('+proj=longlat'))

# Extract neighborhood names for left join later
map_labels <- as.data.frame(neighborhoods)[1:2]
census_labels <- as.data.frame(census_tracts)["census_tra"]
# Test case
latlong <- tibble(index = 1:2,
                  Latitude = c(41.981595,41.849820), 
                  Longitude = c(-87.665797,-87.633348))

# Plot map to make sure reprojections work as expected
neighborhoods %>%  
  ggplot() + 
  geom_sf() + 
  coord_sf() +
  theme_minimal() +
  geom_point(data = latlong, aes(x = Longitude, y = Latitude))

census_tracts %>%  
  ggplot() + 
  geom_sf() + 
  coord_sf() +
  theme_minimal() +
  geom_point(data = latlong, aes(x = Longitude, y = Latitude))


# Test case
latlong %>% 
  mutate(census_tract = lookup_geometries(Latitude, 
                                          Longitude, 
                                          maps = census_tracts,
                                          return_col = "census_tra"),
         neighborhood = lookup_geometries(Latitude,
                                          Longitude,
                                          maps = neighborhoods,
                                          return_col = "PRI_NEIGH")) %>% 
  left_join(map_labels,
            by = c("neighborhood" = "PRI_NEIGH")) # Add in sec_neigh name too




# Sample description searches
extract_neighborhoods(c("none", 
                        "lake view", 
                        "lakeviewuptown", 
                        "lake view uptown"), 
                      map_labels$PRI_NEIGH, 
                      return_strings = TRUE)



# Demo with scraped data
scraped_data <- read_csv("CL_housing_example.csv") %>% head()
neighborhood_test <- add_geometry_column(scraped_data, maps = neighborhoods, column_name = "neighborhood")

neighborhood_test %>% 
  select(post_id, neighborhood, latitude, longitude, posting_body) %>% 
  mutate(mentioned_nbs = extract_neighborhoods(posting_body, map_labels$PRI_NEIGH)) %>% 
  tidyr::unnest(mentioned_nbs,keep_empty = TRUE)

# Create convex hull from neighborhood data
hull <- make_neighborhood_hulls(neighborhood_test)

# Plot convex hulls
census_tracts %>%  # Map data
  ggplot() + 
  geom_sf() + 
  coord_sf() +
  theme_minimal() +
  geom_point(data = neighborhood_test, aes(x = longitude, y = latitude)) +
  ggforce::geom_mark_hull(data = neighborhood_test, aes(x = longitude, y = latitude, fill = neighborhood)) +
  # geom_polygon(data = hull, aes(x = longitude, y = latitude, fill = neighborhood), alpha = 0.5) +
  # coord_sf(ylim = c(41.82,42.02), xlim = c(-88,-87.5)) +
  theme(legend.position = "none")
