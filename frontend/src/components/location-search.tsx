"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { apiGet } from "@/lib/api-client";
import type { LocationSummary } from "@/types/api";
import { cn } from "@/lib/utils";

interface LocationSearchProps {
  onLocationSelect: (location: LocationSummary) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

export function LocationSearch({
  onLocationSelect,
  placeholder = "Search suburb, city or postcode…",
  autoFocus = false,
}: LocationSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LocationSummary[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nonAuFlag, setNonAuFlag] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Fetch autocomplete results
  const fetchResults = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      setIsOpen(false);
      setError(null);
      setNonAuFlag(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setNonAuFlag(false);

    try {
      // Backend returns a plain array, not wrapped in { results: [] }
      const data = await apiGet<{ results: LocationSummary[] }>(
        `/locations/autocomplete?q=${encodeURIComponent(q)}`,
        null
      );

      const limited = (data.results ?? []).slice(0, 8);

      // Check if any result is outside Australia
      const hasNonAu = limited.some((loc) => loc.country_code !== "AU");
      setNonAuFlag(hasNonAu);

      setResults(limited);
      setIsOpen(limited.length > 0 || hasNonAu);
      setActiveIndex(-1);
    } catch {
      setError("Unable to fetch location suggestions. Please try again.");
      setResults([]);
      setIsOpen(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle input changes with 300ms debounce
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      fetchResults(value);
    }, 300);
  };

  // Select a location from the dropdown
  const handleSelect = (location: LocationSummary) => {
    setQuery(location.display_name || `${location.suburb ?? location.city}, ${location.state}`);
    setResults([]);
    setIsOpen(false);
    setError(null);
    setNonAuFlag(false);
    setActiveIndex(-1);
    onLocationSelect(location);
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) return;

    const auResults = results.filter((loc) => loc.country_code === "AU");

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, auResults.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex >= 0 && auResults[activeIndex]) {
          handleSelect(auResults[activeIndex]);
        }
        break;
      case "Escape":
        setIsOpen(false);
        setActiveIndex(-1);
        break;
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Scroll active item into view
  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const item = listRef.current.children[activeIndex] as HTMLElement;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const auResults = results.filter((loc) => loc.country_code === "AU");

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Search input with loading spinner */}
      <div className="relative">
        <Input
          type="text"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          autoComplete="off"
          aria-autocomplete="list"
          aria-expanded={isOpen}
          aria-controls="location-search-listbox"
          aria-activedescendant={
            activeIndex >= 0 ? `location-option-${activeIndex}` : undefined
          }
          role="combobox"
          className="pr-8"
        />
        {isLoading && (
          <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
            <svg
              className="h-4 w-4 animate-spin text-muted-foreground"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border border-border bg-popover shadow-md">
          {error ? (
            <div className="px-3 py-2 text-sm text-destructive">{error}</div>
          ) : nonAuFlag && auResults.length === 0 ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Location not in Australia
            </div>
          ) : (
            <ul
              id="location-search-listbox"
              ref={listRef}
              role="listbox"
              aria-label="Location suggestions"
              className="max-h-60 overflow-auto py-1"
            >
              {auResults.map((location, index) => (
                <li
                  key={location.id}
                  id={`location-option-${index}`}
                  role="option"
                  aria-selected={activeIndex === index}
                  onMouseDown={(e) => {
                    // Prevent input blur before click registers
                    e.preventDefault();
                    handleSelect(location);
                  }}
                  className={cn(
                    "cursor-pointer px-3 py-2 text-sm transition-colors",
                    activeIndex === index
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <span className="font-medium">
                    {location.suburb ?? location.city}
                  </span>
                  <span className="text-muted-foreground">
                    {location.suburb ? `, ${location.city}` : ""}{" "}
                    {location.state}
                    {location.postcode ? ` ${location.postcode}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
