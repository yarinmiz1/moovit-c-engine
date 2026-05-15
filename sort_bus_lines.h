#ifndef EX2_REPO_SORTBUSLINES_H
#define EX2_REPO_SORTBUSLINES_H
// write only between #define EX2_REPO_SORTBUSLINES_H and #endif //EX2_REPO_SORTBUSLINES_H
#include <string.h>
#define NAME_LEN 21
/**
 * Represents a bus line with its identifying name and performance metrics.
 * name: A unique string identifier for the bus line.
 * distance: The total distance of the route.
 * duration: The time it takes to complete the route.
 * frequency: How often the bus runs.
 */
typedef struct BusLine
{
    char name[NAME_LEN];
    int distance, duration, frequency;
} BusLine;

/**
 * Defines the available criteria for sorting bus lines.
 * DISTANCE: Sort by the route distance.
 * DURATION: Sort by the trip duration.
 * FREQUENCY: Sort by the bus frequency.
 */

typedef enum SortType
{
    DISTANCE,
    DURATION,
    FREQUENCY
} SortType;

/**
 * Sorts an array of BusLine structures by name in lexicographical order using the bubble sort algorithm.
 * @param start Pointer to the first element in the array segment.
 * @param end Pointer to the last element in the array segment.
 */
void bus_bubble_sort (BusLine *start, BusLine *end);

/**
 * Sorts an array of BusLine structures based on a specific sort type using the quick sort algorithm.
 * @param start Pointer to the first element in the array segment.
 * @param end Pointer to the last element in the array segment.
 * @param sort_type The criteria to sort by (DISTANCE, DURATION, or FREQUENCY).
 */
void bus_quick_sort (BusLine *start, BusLine *end, SortType sort_type);

/**
 * Swaps the contents of two BusLine structures in memory.
 * @param first Pointer to the first BusLine.
 * @param second Pointer to the second BusLine.
 */
void swap (BusLine *first, BusLine *second);

/**
 * Partitions the array around a pivot element for the quick sort algorithm.
 * @param start Pointer to the first element in the array segment.
 * @param end Pointer to the last element (pivot) in the array segment.
 * @param sort_type The criteria used for comparing the elements.
 * @return Pointer to the final, sorted position of the pivot element.
 */
BusLine *partition (BusLine *start, BusLine *end, SortType sort_type);
// write only between #define EX2_REPO_SORTBUSLINES_H and #endif //EX2_REPO_SORTBUSLINES_H
#endif //EX2_REPO_SORTBUSLINES_H
