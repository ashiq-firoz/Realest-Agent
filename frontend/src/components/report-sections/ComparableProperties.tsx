import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Building2 } from "lucide-react";
import type { PropertyListing } from "@/types/api";

interface ComparablePropertiesProps {
  properties: PropertyListing[];
}

export function ComparableProperties({ properties }: ComparablePropertiesProps) {
  return (
    <Card className="shadow-lg border-slate-200/60 dark:border-slate-800/60 overflow-hidden">
      <CardHeader className="bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-xl">
            <Building2 className="w-5 h-5" />
          </div>
          <CardTitle className="text-xl">Comparable Properties</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50/50 dark:bg-slate-900/20 hover:bg-slate-50/50 dark:hover:bg-slate-900/20">
              <TableHead className="font-semibold">Address</TableHead>
              <TableHead className="font-semibold text-right">Price</TableHead>
              <TableHead className="font-semibold text-center">Beds</TableHead>
              <TableHead className="font-semibold text-center">Baths</TableHead>
              <TableHead className="font-semibold text-center">Type</TableHead>
              <TableHead className="font-semibold text-right">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {properties.map((property, idx) => (
              <TableRow key={idx}>
                <TableCell className="font-medium text-slate-900 dark:text-slate-100">
                  {property.address}
                </TableCell>
                <TableCell className="text-right font-semibold text-indigo-600 dark:text-indigo-400">
                  {property.price}
                </TableCell>
                <TableCell className="text-center text-slate-600 dark:text-slate-400">
                  {property.beds}
                </TableCell>
                <TableCell className="text-center text-slate-600 dark:text-slate-400">
                  {property.baths}
                </TableCell>
                <TableCell className="text-center">
                  <span className="capitalize text-slate-600 dark:text-slate-400">{property.property_type}</span>
                </TableCell>
                <TableCell className="text-right">
                  <Badge 
                    variant={property.listing_type === 'sold' ? 'secondary' : 'default'}
                    className={
                      property.listing_type === 'sold' 
                        ? 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' 
                        : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 hover:bg-emerald-200'
                    }
                  >
                    {property.listing_type}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
            {properties.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-slate-500 px-6">
                  No comparable property listings are available for this location.
                  <span className="block text-xs text-slate-400 mt-1">
                    Live listings come from PropertyLens; none were returned for this area.
                  </span>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
