#include "sort_bus_lines.h"

void swap (BusLine *first, BusLine *second)
{
    BusLine temp = *first;
    *first = *second;
    *second = temp;
}

BusLine *partition (BusLine *start, BusLine *end, SortType sort_type) {
    BusLine *insert_pos = start;
    BusLine *current_pos = start;
    switch (sort_type) {
        case DISTANCE:
            while (current_pos < end)
            {
                if (current_pos->distance < end->distance)
                {
                    swap (insert_pos, current_pos);
                    insert_pos +=1;
                }
                current_pos += 1;
            }
            swap(insert_pos, end);
            break;
        case DURATION:
            while (current_pos < end)
            {
                if (current_pos->duration < end->duration)
                {
                    swap (insert_pos, current_pos);
                    insert_pos +=1;
                }
                current_pos += 1;
            }
            swap(insert_pos, end);
            break;
        case FREQUENCY:
            while (current_pos < end)
            {
                if (current_pos->frequency < end->frequency)
                {
                    swap (insert_pos, current_pos);
                    insert_pos +=1;
                }
                current_pos += 1;
            }
            swap(insert_pos, end);
            break;
    }
    return insert_pos;
}

void bus_quick_sort (BusLine *start, BusLine *end, SortType sort_type)
{
    if (start >= end)
    {
        return;
    }
    BusLine *pivot = partition (start,end,sort_type);
    bus_quick_sort(start,pivot-1,sort_type);
    bus_quick_sort((pivot+1), end, sort_type);
}


void bus_bubble_sort (BusLine *start, BusLine *end)
{
    if (start >= end)
    {
        return;
    }
    BusLine *runner_1 = start;
    BusLine *runner_2 = start+1;
    while (runner_1 < end)
    {
        if (strcmp(runner_1->name, runner_2->name) > 0)
        {
            swap (runner_1, runner_2);
        }
        runner_1 +=1;
        runner_2 +=1;
    }
    bus_bubble_sort(start, end-1);
}