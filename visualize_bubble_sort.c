#include <stdio.h>
#include <string.h>
#include "sort_bus_lines.h"

// Helper function to print the current state of the array with fake hexadecimal addresses
void print_array_state(BusLine *base_arr, int total_size, BusLine *start, BusLine *end, BusLine *run1, BusLine *run2) {
    printf("\n--- Current Memory State ---\n");
    for (int i = 0; i < total_size; i++) {
        // Calculate fake addresses for visualization (0x1000, 0x1040, 0x1080)
        int fake_address = 0x1000 + (i * 0x40);
        
        // Determine pointer labels pointing to this specific cell
        char labels[100] = "";
        if (&base_arr[i] == start) strncat(labels, "[start] ", sizeof(labels) - strlen(labels) - 1);
        if (&base_arr[i] == end) strncat(labels, "[end] ", sizeof(labels) - strlen(labels) - 1);
        if (&base_arr[i] == run1) strncat(labels, "[run_1] ", sizeof(labels) - strlen(labels) - 1);
        if (&base_arr[i] == run2) strncat(labels, "[run_2] ", sizeof(labels) - strlen(labels) - 1);
        
        printf("0x%04X | %-10s | %s\n", fake_address, base_arr[i].name, labels);
    }
    printf("----------------------------\n");
}

// Visualized version of bubble sort
void visual_bubble_sort(BusLine *base_arr, int total_size, BusLine *start, BusLine *end) {
    if (start >= end) {
        printf("\n=> Base case reached: start >= end. Segment sorting complete.\n");
        return;
    }
    
    BusLine *runner_1 = start;
    BusLine *runner_2 = start + 1;
    
    while (runner_1 < end) {
        print_array_state(base_arr, total_size, start, end, runner_1, runner_2);
        
        printf("\nAction: Comparing \"%s\" and \"%s\"\n", runner_1->name, runner_2->name);
        
        if (strcmp(runner_1->name, runner_2->name) > 0) {
            printf("Result: strcmp > 0. SWAP TRIGGERED!\n");
            
            // Perform the swap
            BusLine temp = *runner_1;
            *runner_1 = *runner_2;
            *runner_2 = temp;
            
            printf("State immediately after swap:\n");
            print_array_state(base_arr, total_size, start, end, runner_1, runner_2);
        } else {
            printf("Result: strcmp <= 0. No swap needed.\n");
        }
        
        runner_1 += 1;
        runner_2 += 1;
        printf("\n=> Advancing runner_1 and runner_2 pointers...\n");
    }
    
    printf("\n--- End of Pass. Calling recursively with (end - 1) ---\n");
    visual_bubble_sort(base_arr, total_size, start, end - 1);
}

int main() {
    // Initialize the test array
    BusLine buses[3] = {
        {"Dan", 10, 10, 10},
        {"Alice", 20, 20, 20},
        {"Charlie", 30, 30, 30}
    };
    
    printf("=========================================\n");
    printf("  BUBBLE SORT POINTER VISUALIZATION\n");
    printf("=========================================\n");
    
    // Start the visualized sort (pointers initialized to first and last element)
    visual_bubble_sort(buses, 3, &buses[0], &buses[2]);
    
    printf("\n=========================================\n");
    printf("  FINAL SORTED ARRAY\n");
    printf("=========================================\n");
    print_array_state(buses, 3, NULL, NULL, NULL, NULL);
    
    return 0;
}
