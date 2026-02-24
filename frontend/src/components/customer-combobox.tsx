'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, User, Loader2, ChevronsUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from '@/components/ui/command';
import { customersApi } from '@/lib/api';
import type { Customer } from '@/types';

interface CustomerComboboxProps {
  value?: string;
  onSelect: (customer: Customer) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function CustomerCombobox({
  value,
  onSelect,
  placeholder = 'Search customer by name, phone, or code...',
  disabled = false,
}: CustomerComboboxProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [results, setResults] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState('');

  // Debounced search
  useEffect(() => {
    if (search.length < 2) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await customersApi.list({ search, size: 20 });
        setResults(data.items || []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  // Load selected customer label on mount if value is set
  useEffect(() => {
    if (value && !selectedLabel) {
      customersApi.getById(value).then((customer) => {
        setSelectedLabel(
          `${customer.name || customer.full_name || ''} — ${customer.phone}`
        );
      }).catch(() => {});
    }
  }, [value, selectedLabel]);

  const handleSelect = useCallback(
    (customer: Customer) => {
      setSelectedLabel(
        `${customer.name || customer.full_name || ''} — ${customer.phone}`
      );
      onSelect(customer);
      setOpen(false);
      setSearch('');
    },
    [onSelect]
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between font-normal"
          disabled={disabled}
        >
          {selectedLabel || (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Enter name, phone, or code..."
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            {loading && (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            )}
            <CommandEmpty>
              {search.length < 2
                ? 'Type at least 2 characters to search'
                : 'No customers found'}
            </CommandEmpty>
            <CommandGroup heading="Customers">
              {results.map((customer) => (
                <CommandItem
                  key={customer.id}
                  value={customer.id}
                  onSelect={() => handleSelect(customer)}
                  className="cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted">
                      <User className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-medium truncate">
                        {customer.name || customer.full_name}
                      </div>
                      <div className="text-xs text-muted-foreground truncate">
                        {customer.phone}
                        {customer.customer_code && ` · ${customer.customer_code}`}
                      </div>
                    </div>
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
