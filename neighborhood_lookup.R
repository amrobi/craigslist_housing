library(sf)      # For shapefile compatibility
library(rgdal)   # For CRS projection
library(dplyr)   # Data wrangling etc.
library(ggplot2) # Plotting
library(readr)   # Read in csv
library(tidyr)   # Unnest
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


# Lookup neighborhoods in descriptions
extract_neighborhoods <- function(descriptions, neighborhood_names, return_strings = TRUE){
  lapply(descriptions,
         function(description){
           # Standardize everything to lowercase before searching
           description <- tolower(description)
           neighborhood_names <- vapply(neighborhood_names, tolower, "char")
           is_mentioned <- vapply(neighborhood_names, 
                                  function(nb) grepl(nb, description), 
                                  TRUE, 
                                  USE.NAMES=TRUE # Associates nb names to bool values
                                  )
           mentioned_neighborhoods <- names(is_mentioned)[is_mentioned]
           if (return_strings) return(mentioned_neighborhoods)
           return(is_mentioned)
         }
  )
  
  # Follow this with unnest(df, cols = neighborhood_column, keep_empty = TRUE)
}

# Sample description searches
extract_neighborhoods(c("none", 
                        "lake view", 
                        "lakeviewuptown", 
                        "lake view uptown"), 
                      neighborhood_names$PRI_NEIGH, 
                      return_strings = TRUE)

neighborhood_test %>% 
  select(post_id, neighborhood, latitude, longitude, posting_body) %>% 
  mutate(mentioned_nbs = extract_neighborhoods(posting_body, neighborhood_names$PRI_NEIGH)) %>% 
  tidyr::unnest(mentioned_nbs,keep_empty = TRUE)

# Demo with scraped data
scraped_data <- read_csv("CL_housing_example.csv") %>% head()
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
