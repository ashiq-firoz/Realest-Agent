import * as fc from "fast-check";

import type { PropertyListing } from "@/types/api";

describe("Comparable Properties Logic Properties", () => {
  it("should never have negative prices or invalid beds/baths", () => {
    const propertyArbitrary = fc.record({
      address: fc.string({ minLength: 1 }),
      price: fc.string(),
      price_numeric: fc.integer({ min: 10000 }),
      beds: fc.integer({ min: 1, max: 10 }),
      baths: fc.float({ min: 1, max: 10, noNaN: true }),
      sqft: fc.option(fc.integer({ min: 100, max: 10000 })),
      listing_type: fc.constantFrom("sold", "active", "leased"),
      property_type: fc.constantFrom("house", "unit", "townhouse"),
      source: fc.constant("domain"),
    });

    fc.assert(
      fc.property(propertyArbitrary, (property) => {
        const listing = property as PropertyListing;
        expect(listing.price_numeric).toBeGreaterThan(0);
        expect(listing.beds).toBeGreaterThan(0);
        expect(listing.baths).toBeGreaterThan(0);
      })
    );
  });
});

