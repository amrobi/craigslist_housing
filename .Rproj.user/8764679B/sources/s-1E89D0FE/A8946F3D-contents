#' Lookup singular geometry
#' 
#' Given a latitude and longitude value, as well as a list of maps read in
#' from a shape file and projected to lat/long space, lookup which area
#' the point belongs to using point in polygon calculations, returning the value
#' in return_col. 
#'
#' @param lat Latitude value
#' @param long Longitude value
#' @param maps Shapefile geometries read in from a .shp
#' @param return_col Which column you want (defaults to PRI_NEIGH for use with
#' neighborhood geometries)
#'
#' @return String value in return_col from maps for the area the point is in
lookup_geometry <- function(lat, long, maps, return_col = "PRI_NEIGH") {
  # ~ 20ms per lookup
  spatial_point <- st_point(c(long, lat)) # Note the ordering
  
  if (is.na(lat) | is.na(long))
    return(NA_character_)
  
  geometry_index <- 
    as.integer(
      suppressMessages( # Hide planar assumption message
        sf::st_intersects(spatial_point, 
                          maps[["geometry"]], 
                          sparse = TRUE # To return index not a matrix
        )
      )
    )
  if (is.na(geometry_index)) return(NA_character_) # Point is not in a chicago neighborhood
  maps[[geometry_index, return_col]]
}

#' Lookup geometries
#' 
#' Just a vectorized version of lookup_geometry
#'
#' @param lats Vector of latitudes
#' @param longs Vector of longitudes
#' @param maps Maps to use
#' @param return_col Which column value to return (default PRI_NEIGH)
#'
#' @return Vector of strings from return_col
lookup_geometries <- function(lats, longs, maps, return_col) {
  if (length(lats) != length(longs))
    stop("Uneven number of lat/long values")
  
  vapply(seq_along(lats),
         function(i) 
           lookup_geometry(lats[[i]], longs[[i]], maps, return_col),
         "character"
  )
  
}

#' Add column from geometry lookup
#'
#' @param scraped_data Scraped dataframe from craigslet
#' @param maps maps to use
#' @param column_name name of the column you want to add to the dataframe, defaults to "neighborhood"
#' @param return_col column from the map that you want to pull values from, to pass to lookup_geometries
#'
#' @return Dataframe with added column specified from column_name, with values from maps$return_col
add_geometry_column <- function(scraped_data, maps, column_name = "neighborhood", return_col = "PRI_NEIGH") {
  scraped_data %>%
    mutate(!!column_name := lookup_geometries(latitude, 
                                              longitude, 
                                              maps = maps,
                                              return_col = return_col))
}

# Calculate convex hulls for all neighborhoods, requires filtering out NAs
#' Calculate convex hulls for neighborhoods
#'
#' Given a dataframe with latitude and longitude columns and a grouping column
#' (typically neighborhood names) return the subset of the dataframe that
#' comprises the points lying on the outer hull. Note: will be a smaller dataframe,
#' so assign it to a new variable name
#'
#' @param neighborhood_data Scraped data with latitude, longitude, and grouping columns
#' @param neighborhood_column Name of the neighborhood column
#'
#' @return A dataframe of hulls for each level of the grouping column
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


#' Lookup neighborhoods from descriptions
#'
#' Given a vector of text description, return a list of character vectors of the
#' neighborhoods found in the descriptions. If return_strings is FALSE, return
#' a list of logical vectors where TRUE indicates that the neighborhood was detected
#'
#' Preprocessing: lowercase all
#'
#' @param descriptions Vector of strings to search through
#' @param map_labels List of labels to look for
#' @param return_strings TRUE to return char vectors, FALSE to return logical vectors
#'
#' @return List of char or logical vectors
extract_neighborhoods <- function(descriptions, map_labels, return_strings = TRUE){
  lapply(descriptions,
         function(description){
           # Standardize everything to lowercase before searching
           description <- tolower(description)
           map_labels <- vapply(map_labels, tolower, "char")
           is_mentioned <- vapply(map_labels, 
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
