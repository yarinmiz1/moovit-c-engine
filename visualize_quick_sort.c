#include <stdio.h>
#include <string.h>
#include "sort_bus_lines.h"

// Helper function to print the current state of the array with fake hexadecimal addresses
void print_array_state(BusLine *base_arr, int total_size, BusLine *start, BusLine *end, BusLine *insert, BusLine *current) {
    printf("\nMemory Grid:\n");
    for (int i = 0; i < total_size; i++) {
        // Calculate fake addresses for visualization starting at 0x2000
        int fake_address = 0x2000 + (i * 0x40);
        
        // Determine pointer labels pointing to this specific cell
        char labels[100] = "";
        if (&base_arr[i] == start) strncat(labels, "[start] ", sizeof(labels) - strlen(labels) - 1);
        if (&base_arr[i] == end) strncat(labels, "[end] ", sizeof(labels) - strlen(labels) - 1);
        if (&base_arr[i] == insert) strncat(labels, "[insert_pos] ", sizeof(labels) - strlen(labels) - 1);
        if (&base_arr[i] == current) strncat(labels, "[current_pos] ", sizeof(labels) - strlen(labels) - 1);
        
        printf("0x%04X | %2d | %s\n", fake_address, base_arr[i].distance, labels);
    }
    printf("------------------------------------------------------\n");
}

// Visualized version of the quick sort partition logic
BusLine* visual_partition(BusLine *base_arr, int total_size, BusLine *start, BusLine *end) {
    BusLine *insert_pos = start;
    BusLine *current_pos = start;
    int pivot_value = end->distance;
    
    printf("\n### Setup Phase\n");
    printf("When partition is first called, we define our pointers and our pivot value.\n");
    printf("Pivot Value (end->distance): %d\n", pivot_value);
    
    int step = 1;
    while (current_pos < end) {
        printf("\n### Step %d\n", step++);
        print_array_state(base_arr, total_size, start, end, insert_pos, current_pos);
        
        printf("Action: Compare current_pos (%d) against Pivot (%d).\n", current_pos->distance, pivot_value);
        
        if (current_pos->distance < pivot_value) {
            printf("Result: %d IS less than %d! SWAP TRIGGERED.\n", current_pos->distance, pivot_value);
            printf("The struct at insert_pos swaps with the struct at current_pos.\n");
            
            // Perform the swap
            BusLine temp = *insert_pos;
            *insert_pos = *current_pos;
            *current_pos = temp;
            
            insert_pos += 1;
            printf("Both insert_pos and current_pos step forward.\n");
        } else {
            printf("Result: %d is NOT less than %d. No swap.\n", current_pos->distance, pivot_value);
            printf("Only current_pos steps forward. insert_pos stays put.\n");
        }
        
        current_pos += 1;
    }
    
    printf("\n### Step %d: Exiting the Loop & Final Swap\n", step);
    printf("current_pos is now at end. The while loop breaks.\n");
    printf("Action: swap(insert_pos, end)\n");
    
    // Final swap to place pivot
    BusLine temp = *insert_pos;
    *insert_pos = *end;
    *end = temp;
    
    printf("\nFINAL Memory Grid:\n");
    for (int i = 0; i < total_size; i++) {
        int fake_address = 0x2000 + (i * 0x40);
        char labels[100] = "";
        if (&base_arr[i] == insert_pos) strncat(labels, "<-- FINAL PIVOT POSITION", sizeof(labels) - strlen(labels) - 1);
        printf("0x%04X | %2d | %s\n", fake_address, base_arr[i].distance, labels);
    }
    printf("------------------------------------------------------\n");
    
    // Calculate the fake hex address of the final pivot for the return message
    int fake_pivot_address = 0x2000 + ((int)(insert_pos - base_arr) * 0x40);
    printf("\n### The Return Statement\n");
    printf("The partition function returns insert_pos (memory address 0x%04X).\n", fake_pivot_address);
    printf("The pivot value (%d) is exactly where it belongs!\n", pivot_value);
    
    return insert_pos;
}

int main() {
    // Initialize the test array focusing purely on distance
    BusLine buses[4] = {
        {"Line1", 50, 0, 0},
        {"Line2", 20, 0, 0},
        {"Line3", 60, 0, 0},
        {"Line4", 40, 0, 0}
    };
    
    printf("======================================================\n");
    printf("  QUICK SORT PARTITION MEMORY VISUALIZATION\n");
    printf("======================================================\n");
    
    // Start the visualized partition
    visual_partition(buses, 4, &buses[0], &buses[3]);
    
    return 0;
}
