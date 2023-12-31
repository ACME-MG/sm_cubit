"""
 Title:         Improver
 Description:   Improves the quality of the grid
 Author:        Janzen Choi

"""

# Libraries
import sm_cubit.maths.pixel_maths as pixel_maths
from random import randint
from copy import deepcopy

def clean_pixel_grid(pixel_grid:list) -> list:
    """
    Cleans the pixel grid by replacing stray void / live pixels
    
    Parameters:
    * `pixel_grid`: The uncleaned grid of pixels
    
    Returns the cleaned pixel grid
    """

    # Dimensions of the pixel grid
    x_size = len(pixel_grid[0])
    y_size = len(pixel_grid)
    
    # Iterate through each pixel
    for row in range(y_size):
        for col in range(x_size):

            # Ignore if it's added material
            if pixel_grid[row][col] == pixel_maths.UNORIENTED_PIXEL_ID:
                continue

            # Evaluate neighbouring pixels
            neighbours = pixel_maths.get_neighbours(col, row, x_size, y_size)
            void_neighbours = [n for n in neighbours if pixel_grid[n[1]][n[0]] == pixel_maths.VOID_PIXEL_ID]
            num_void = len(void_neighbours)
            
            # If half (or less) of the neighbours are void, then fill a void pixel
            if pixel_grid[row][col] == pixel_maths.VOID_PIXEL_ID and num_void <= len(neighbours) / 2:
                copy = neighbours[randint(0, len(neighbours) - 1)]
                if pixel_grid[copy[1]][copy[0]] == pixel_maths.UNORIENTED_PIXEL_ID:
                    continue
                pixel_grid[row][col] = pixel_grid[copy[1]][copy[0]]

            # If more than half of the neighbours are void, then remove a live pixel
            if pixel_grid[row][col] != pixel_maths.VOID_PIXEL_ID and num_void > len(neighbours) / 2:
                pixel_grid[row][col] = pixel_maths.VOID_PIXEL_ID

    # Return cleaned pixel grid
    return pixel_grid

def smoothen_edges(pixel_grid:list) -> list:
    """
    Smoothen the edges of grains by merging pixels
    
    Parameters:
    * `pixel_grid`: The unsmoothed grid of pixels
    
    Returns the smoothed pixel grid
    """

    # Dimensions of the pixel grid
    x_size = len(pixel_grid[0])
    y_size = len(pixel_grid)
    
    # Iterate through each pixel
    for row in range(y_size):
        for col in range(x_size):
        
            # Ignore if it's added material
            if pixel_grid[row][col] == pixel_maths.UNORIENTED_PIXEL_ID:
                continue

            # Evaluate neighbouring pixels
            neighbours = pixel_maths.get_neighbours(col, row, x_size, y_size)
            foreign_neighbours = [n for n in neighbours if pixel_grid[n[1]][n[0]] != pixel_grid[row][col]]

            # If there are more than 2 foreign neighbours, get absorbed
            if len(foreign_neighbours) > 2:
                foreign = foreign_neighbours[randint(0, len(foreign_neighbours) - 1)]
                if pixel_grid[foreign[1]][foreign[0]] == pixel_maths.UNORIENTED_PIXEL_ID:
                    continue
                pixel_grid[row][col] = pixel_grid[foreign[1]][foreign[0]]

    # Return cleaned pixel grid
    return pixel_grid

def pad_edges(pixel_grid:list) -> list:
    """
    Pads the pixel grid by replicating unvoided pixels
    
    Parameters:
    * `pixel_grid`: The unpadded grid of pixels
    
    Returns the padded pixel grid
    """
    
    # Dimensions of the pixel grid
    x_size = len(pixel_grid[0])
    y_size = len(pixel_grid)
    
    # Replicate it
    padded_pixel_grid = pixel_maths.get_void_pixel_grid(x_size, y_size)

    # Iterate through each pixel
    for row in range(y_size):
        for col in range(x_size):

            # If live, copy and skip
            if pixel_grid[row][col] != pixel_maths.VOID_PIXEL_ID:
                padded_pixel_grid[row][col] = pixel_grid[row][col]
                continue

            # Get live neighbouring pixels
            neighbours = pixel_maths.get_neighbours(col, row, x_size, y_size)
            live_neighbours = [n for n in neighbours if pixel_grid[n[1]][n[0]] != pixel_maths.VOID_PIXEL_ID]

            # If there is a live neighbour, then fill this void pixel
            if len(live_neighbours) > 0:
                copy = live_neighbours[randint(0, len(live_neighbours) - 1)]
                padded_pixel_grid[row][col] = pixel_grid[copy[1]][copy[0]]
    
    # Return padded pixel grid
    return padded_pixel_grid

def get_sorted_grain_id_list(pixel_grid:list) -> tuple:
    """
    Gets sorted list of grain ids without voids
    
    Parameters:
    * `pixel_grid`: The unpadded grid of pixels
    
    Returns the sorted IDs and the flattened IDs
    """
    flattened = [pixel for pixel_list in pixel_grid for pixel in pixel_list]
    id_list = list(set(flattened))
    if pixel_maths.VOID_PIXEL_ID in id_list:
        id_list.remove(pixel_maths.VOID_PIXEL_ID)
    id_list.sort()
    return id_list, flattened

def remove_small_grains(pixel_grid:list, threshold:int) -> list:
    """
    Removes small grains
    
    Parameters:
    * `pixel_grid`: The unremoved grid of pixels
    * `threshold`:  The grain size threshold to start removing grains
    
    Returns the pixel grid without the small grains
    """
    
    # Initialise
    id_list, flattened = get_sorted_grain_id_list(pixel_grid)
    x_size = len(pixel_grid[0])
    y_size = len(pixel_grid)

    # Remove grains under size threshold
    for id in id_list:

        # Only consider grains under threshold
        if flattened.count(id) >= threshold:
            continue

        # Get the coordinates of all the pixels
        x_list, y_list = [], []
        for row in range(y_size):
            for col in range(x_size):
                if pixel_grid[row][col] != id:
                    continue
                x_list.append(col)
                y_list.append(row)

        # Find most neighbouring grain
        neighbours = pixel_maths.get_all_neighbours(x_list, y_list, x_size, y_size)
        neighbour_ids = [pixel_grid[neighbour[1]][neighbour[0]] for neighbour in neighbours]
        most_neighbouring = max(set(neighbour_ids), key=neighbour_ids.count)

        # Replace coordinates of small grain
        for i in range(len(x_list)):
            pixel_grid[y_list[i]][x_list[i]] = most_neighbouring
    
    # Return the new pixel grid
    return pixel_grid

def merge_grains(pixel_grid:list, grain_map:dict, threshold:int=10) -> list:
    """
    Merges commonly oriented grains
    
    Parameters:
    * `pixel_grid`: The unmerged grid of pixels
    * `grain_map`:  The mapping from grain IDs to their orientations
    * `threshold`:  The grain size threshold to start removing grains
    
    Returns the pixel grid with the merged grains
    """

    # Intialise
    id_list, _ = get_sorted_grain_id_list(pixel_grid)
    new_pixel_grid = deepcopy(pixel_grid)
    merge_map = {}
    
    # Identify grains to merge
    for i in range(len(id_list)):
        orientation_1 = grain_map[id_list[i]].get_orientation()
        for j in range(i+1, len(id_list)):
            orientation_2 = grain_map[id_list[j]].get_orientation()
            error = sum([abs(orientation_1[k] - orientation_2[k]) for k in range(3)])
            if error < threshold:
                if id_list[i] in merge_map.keys():
                    merge_map[id_list[i]] += [id_list[j]]
                else:
                    merge_map[id_list[i]] = [id_list[j]]

    # Merge the grains in the pixel grid
    for id in merge_map.keys():
        for i in range(len(pixel_grid)):
            for j in range(len(pixel_grid[0])):
                if new_pixel_grid[i][j] in merge_map[id]:
                    new_pixel_grid[i][j] = id
    
    # Print summary and return
    new_id_list, _ = get_sorted_grain_id_list(new_pixel_grid)
    print("=========================")
    print(f"Merged from {len(id_list)} grains to {len(new_id_list)} grains")
    print("=========================")
    return new_pixel_grid
