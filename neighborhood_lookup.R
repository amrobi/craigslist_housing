library(sf)      # For shapefile compatibility
library(rgdal)   # For CRS projection
library(dplyr)   # Data wrangling etc.
library(ggplot2) # Plotting
library(readr)   # Read in csv

# Load in neighborhood boundary data, convert from US Census to lat/long
neighborhoods <- 
  sf::st_read('maps/Neighborhoods_2012b.shp') %>% 
  st_transform(CRS('+proj=longlat'))

# Extract neighborhood names for left join later
neighborhood_names <- as.data.frame(neighborhoods)[1:2]

# Test case
latlong <- tibble(index = 1:2,
                  Latitude = c(41.981595,41.849820), 
                  Longitude = c(-87.665797,-87.633348))

# Plot map to make sure it looks good
neighborhoods %>%  
  ggplot() + 
  geom_sf() + 
  coord_sf() +
  theme_minimal() +
  geom_point(data = latlong, aes(x = Longitude, y = Latitude))

# Look up which neighborhood a point with given lat/long coordinates is in
# latitudes are around 41, longitudes are around -87
lookup_neighborhood <- function(lat, long, neighborhood_maps) {
  # ~ 20ms per lookup
  spatial_point <- st_point(c(long, lat)) # Note the ordering
  
  if (is.na(lat) | is.na(long))
    return(NA_character_)
  
  neighborhood_index <- 
    as.integer(
      suppressMessages( # Hide planar assumption message
        sf::st_intersects(spatial_point, 
                          neighborhood_maps[["geometry"]], 
                          sparse = TRUE # To return index not a matrix
        )
      )
    )
  if (is.na(neighborhood_index)) return(NA_character_) # Point is not in a chicago neighborhood
  neighborhood_maps[[neighborhood_index, "PRI_NEIGH"]]
}

# Vectorized neighborhood lookup for use in mutate call
lookup_neighborhoods <- function(lats, longs, neighborhood_maps) {
  if (length(lats) != length(longs))
    stop("Uneven number of lat/long values")
  
  vapply(seq_along(lats),
         function(i) 
           lookup_neighborhood(lats[[i]], longs[[i]], neighborhood_maps),
         "character"
  )
  
}

# Test case
latlong %>% 
  mutate(neighborhood = lookup_neighborhoods(Latitude, 
                                             Longitude, 
                                             neighborhood_maps = neighborhoods)) %>% 
  left_join(neighborhood_names,
            by = c("neighborhood" = "PRI_NEIGH")) # Add in sec_neigh name too



# Add a column for the neighborhoods as determined by point in polygon
add_neighborhood_column <- function(scraped_data, neighborhood_column = "neighborhood") {
  scraped_data %>%
    mutate(!!neighborhood_column := lookup_neighborhoods(latitude, 
                                                         longitude, 
                                                         neighborhood_maps = neighborhoods))
}

# Calculate convex hulls for all neighborhoods, requires filtering out NAs
make_neighborhood_hulls <- function(neighborhood_data, neighborhood_column = "neighborhood") {
  if (!all(c('latitude','longitude') %in% names(neighborhood_data)))
    stop("Columns latitude and longitude not found")
  if (!neighborhood_column %in% names(neighborhood_data))
    stop("Must add neighborhood column before calculating convex hull")
  
  neighborhood_data %>%
    filter(!is.na(latitude), 
           !is.na(longitude), 
           !is.na(!!sym(neighborhood_column))) %>% 
    group_by(!!sym(neighborhood_column)) %>% 
    slice(chull(longitude, latitude))
  
}

# Demo with scraped data
scraped_data <- read_csv("CL_housing.csv")
neighborhood_test <- add_neighborhood_column(scraped_data)

# Create convex hull from neighborhood data
hull <- make_neighborhood_hulls(neighborhood_test)

# Plot convex hulls
neighborhoods %>%  # Map data
  ggplot() + 
  geom_sf() + 
  coord_sf() +
  theme_minimal() +
  geom_point(data = neighborhood_test, aes(x = longitude, y = latitude), shape=1, alpha=.25) +
  # ggforce::geom_mark_hull(data = neighborhood_test, aes(x = longitude, y = latitude, fill = neighborhood)) +
  geom_polygon(data = hull, aes(x = longitude, y = latitude, fill = neighborhood), alpha = 0.5) +
  coord_sf(ylim = c(41.82,42.02), xlim = c(-88,-87.5)) +
  theme(legend.position = "none")
