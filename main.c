#include "sort_bus_lines.h"
#include "test_bus_lines.h"
#include <stdio.h>
#include <stdlib.h>

#define MAX_LINE_NAME 21
#define EVEN 2
#define MIN_DISTANCE 0
#define MAX_DISTANCE 1000
#define MIN_DURATION 10
#define MAX_DURATION 100
#define MIN_FREQUENCY 1
#define MAX_FREQUENCY 50
#define TIMES_TEN 10
#define MAX_LINE_LENGTH 60
#define NUM_ASCII_START 48
#define NUM_ASCII_END 57
#define LETTER_ASCII_START 97
#define LETTER_ASCII_END 122

/**
 * Checks if the provided command line argument matches one of the valid operations.
 * @param cmd The command string entered by the user.
 * @return 0 if the command is valid, 1 otherwise.
 */
int cmd_check (const char *cmd)
{
    if (strcmp(cmd, "by_duration") == 0)
    {
        return 0;
    }
    else if (strcmp(cmd, "by_distance") == 0)
    {
        return 0;
    }
    else if (strcmp(cmd, "by_frequency") == 0)
    {
        return 0;
    }
    else if (strcmp(cmd, "by_name") == 0)
    {
        return 0;
    }
    else if (strcmp(cmd, "test") == 0)
    {
        return 0;
    }
    return 1;
}

/**
 * Validates that the bus name contains only digits (0-9) and lowercase English letters (a-z).
 * @param arr The string representing the bus name.
 * @return 0 if the name format is valid, 1 if it contains invalid characters.
 */
int cpl_check (const char *arr)
{
    int i = 0;
    while (arr[i] != '\0')
    {
        if ((arr[i] < NUM_ASCII_START)
            || (arr[i] > NUM_ASCII_END
            && arr[i] < LETTER_ASCII_START)
            || (arr[i] > LETTER_ASCII_END))
        {
            fputs ("Error: bus name should contain only digits and small chars\n", stdout);
            return 1;
        }
        i++;
    }
    return 0;
}

/**
 * Validates all fields of a BusLine structure according to the predefined constraints
 * (name format, distance, duration, and frequency limits).
 * @param bus The BusLine structure to be validated.
 * @return 0 if all fields are valid, 1 if any field violates the constraints.
 */
int input_check (const BusLine bus)
{
    if (strcmp (bus.name, "") == 0)
    {
        fputs ("Error: bus name should contains only digits and small chars\n", stdout);
        return 1;
    }
    else if (cpl_check(bus.name) == 1)
    {
        return 1;
    }
    else if (bus.distance < MIN_DISTANCE || bus.distance > MAX_DISTANCE)
    {
        fputs ("Error: bus distance should be an integer between 0 and 1000 (includes)\n", stdout);
        return 1;
    }
    else if (bus.duration < MIN_DURATION || bus.duration > MAX_DURATION)
    {
        fputs ("Error: bus duration should be an integer between 10 and 100 (includes)\n", stdout);
        return 1;
    }
    else if (bus.frequency < MIN_FREQUENCY || bus.frequency > MAX_FREQUENCY)
    {
        fputs ("Error: bus frequency should be an integer between 1 and 50 (includes)\n", stdout);
        return 1;
    }
    return 0;
}

/**
 * Prompts the user to enter the number of bus lines they wish to input.
 * @return The integer number of bus lines entered by the user.
 */
int ask_for_line_number ()
{
    char temp_arr[MAX_LINE_LENGTH] = {0};
    fputs ("Enter number of lines. Then enter\n", stdout);
    fgets (temp_arr, MAX_LINE_LENGTH, stdin);
    int real_line_num = 0;
    sscanf (temp_arr, "%d", &real_line_num);
    return real_line_num;
}

/**
 * Prompts the user to enter the details for each bus line and populates the array.
 * If invalid input is detected, it asks the user to re-enter the details for that specific line.
 * @param bus_lines Pointer to the dynamically allocated array of BusLine structures.
 * @param real_line_num The total number of valid bus lines to collect.
 */
void ask_for_bus_info (BusLine *bus_lines, const int real_line_num)
{
    for (int i = 0; i < real_line_num; i++)
    {
        char temp_arr[MAX_LINE_LENGTH] = {0};
        fputs ("Enter line info. Then enter\n", stdout);
        fgets (temp_arr, MAX_LINE_LENGTH, stdin);
        sscanf (temp_arr, "%20[^,],%d,%d,%d", bus_lines[i].name, &bus_lines[i].distance, &bus_lines[i].duration, &bus_lines[i].frequency);
        if (input_check(bus_lines[i]) == 1)
        {
            i--;
        }
    }
}

/**
 * Prints the formatted result of a specific test (PASSED or FAILED) based on the test's outcome.
 * @param test_num The chronological number of the test being executed (1-8).
 * @param result The outcome of the test (1 for success, 0 for failure).
 * @param test_name A string representing the criteria being tested (e.g., "distance", "name").
 */
void print_test_result (const int test_num, const int result, const char *test_name)
{
    if (result == 0)
    {
        if (test_num % EVEN == 1)
        {
            printf ("TEST %d FAILED: Not sorted by %s\n", test_num, test_name);
        }
        else
        {
            printf ("TEST %d FAILED: Original array element changed\n", test_num);
        }
    }
    if (result == 1)
    {
        if (test_num % EVEN == 1)
        {
            printf ("TEST %d PASSED: The array is Sorted by %s\n", test_num, test_name);
        }
        else
        {
            printf ("TEST %d PASSED: The array has the same items after sorting\n", test_num);
        }
    }
}

/**
 * Executes a comprehensive suite of 8 tests on the bus lines array.
 * It sorts the array by different criteria and verifies both the sorting correctness
 * and that the original array's contents were not modified or lost.
 * @param start Pointer to the first element in the array.
 * @param end Pointer to the last element in the array.
 * @param real_line_num The total number of elements in the array.
 */
void test_execute (BusLine *start, BusLine *end, const int real_line_num)
{
    BusLine *backup = malloc(real_line_num * sizeof(BusLine));
    if (backup == NULL)
    {
        return;
    }
    BusLine *backup_start = backup;
    BusLine *backup_end = backup + real_line_num - 1;
    memcpy (backup_start, start, real_line_num * sizeof(BusLine));
    int test_counter = 1;
    bus_quick_sort(start, end, DISTANCE);
    print_test_result(test_counter++, is_sorted_by_distance(start, end), "distance");
    print_test_result(test_counter++, is_equal(start, end, backup_start, backup_end), "distance");
    bus_quick_sort(start, end, DURATION);
    print_test_result(test_counter++, is_sorted_by_duration(start, end), "duration");
    print_test_result(test_counter++, is_equal(start, end, backup_start, backup_end), "duration");
    bus_quick_sort(start, end, FREQUENCY);
    print_test_result(test_counter++, is_sorted_by_frequency(start, end), "frequency");
    print_test_result(test_counter++, is_equal(start, end, backup_start, backup_end), "frequency");
    bus_bubble_sort(start, end);
    print_test_result(test_counter++, is_sorted_by_name(start, end), "name");
    print_test_result(test_counter, is_equal(start, end, backup_start, backup_end), "name");
    free(backup);
}

/**
 * Routes the program execution to the appropriate sorting algorithm or testing suite
 * based on the user's initial command.
 * @param bus_lines Pointer to the array of BusLine structures.
 * @param cmd The valid command string entered by the user.
 * @param real_line_num The total number of elements in the array.
 */
void cmd_execute (BusLine *bus_lines, const char *cmd, const int real_line_num)
{
    BusLine *end = bus_lines + real_line_num - 1;
    if (strcmp(cmd, "by_distance") == 0)
    {
        bus_quick_sort(bus_lines, end, DISTANCE);
    }
    else if (strcmp(cmd, "by_duration") == 0)
    {
        bus_quick_sort(bus_lines, end, DURATION);
    }
    else if (strcmp(cmd, "by_frequency") == 0)
    {
        bus_quick_sort(bus_lines, end, FREQUENCY);
    }
    else if (strcmp(cmd, "by_name") == 0)
    {
        bus_bubble_sort(bus_lines, end);
    }
    else if (strcmp(cmd, "test") == 0)
    {
        test_execute(bus_lines, end, real_line_num);
    }
}

/**
 * Prints the sorted bus lines array to the standard output in a comma-separated format.
 * @param bus Pointer to the array of BusLine structures to be printed.
 * @param real_line_num The total number of elements in the array.
 */
void print_sorted_result (const BusLine *bus, const int real_line_num)
{
    int count = 0;
    while (count < real_line_num)
    {
        printf ("%s,%d,%d,%d\n", bus[count].name, bus[count].distance, bus[count].duration, bus[count].frequency);
        count++;
    }
}

/**
 * The main entry point of the program.
 * Validates command-line arguments, allocates memory, coordinates the collection
 * of user input, executes the requested command, and ensures memory is freed.
 * @param argc The number of command-line arguments.
 * @param argv The array of command-line argument strings.
 * @return 0 upon successful execution, 1 if an error or invalid usage occurs.
 */
int main (int argc, char *argv[])
{
    if (argc != EVEN)
    {
        fputs ("Usage: There should be exactly one command, the command should be valid by the format; by_duration / by_distance / by_frequency / by_name / test.\n", stdout);
        return EXIT_FAILURE;
    }
    if (cmd_check (argv[1]) == 1)
    {
        fputs ("Usage: Command format must be valid; by_duration / by_distance / by_frequency / by_name / test.\n", stdout);
        return EXIT_FAILURE;
    }
    int real_line_num = ask_for_line_number();
    while (real_line_num <= 0)
    {
        fputs ("Error: Number of lines should be a positive integer\n", stdout);
        real_line_num = ask_for_line_number();
    }
    BusLine *bus_lines = malloc(real_line_num * sizeof(BusLine));
    if (bus_lines == NULL)
    {
        return EXIT_FAILURE;
    }
    ask_for_bus_info(bus_lines, real_line_num);
    cmd_execute (bus_lines, argv[1], real_line_num);
    if (strcmp(argv[1], "test") != 0)
    {
        print_sorted_result(bus_lines, real_line_num);
    }
    free (bus_lines);
    return EXIT_SUCCESS;
}