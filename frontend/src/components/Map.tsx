'use client';

import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';
import L from 'leaflet';

const icon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const SUBURBS = [
  { name: 'Surry Hills', coords: [-33.8833, 151.2117], price: '$1.8M' },
  { name: 'Bondi Beach', coords: [-33.8915, 151.2767], price: '$3.5M' },
  { name: 'Parramatta', coords: [-33.8150, 151.0011], price: '$1.1M' },
  { name: 'Manly', coords: [-33.7962, 151.2828], price: '$4.2M' },
  { name: 'Newtown', coords: [-33.8972, 151.1788], price: '$1.6M' },
];

export default function Map() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div style={{ width: '100%', height: '100%', background: '#0a0a0c' }} />;

  const handleMarkerClick = (suburb: string, price: string) => {
    const query = `Provide a real estate prediction for ${suburb} where average price is currently ${price}. Please incorporate current domestic and international news, economic reports, and global trends that might impact this area.`;
    window.dispatchEvent(new CustomEvent('ASK_AGENT', { detail: { query } }));
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer 
        center={[-33.8688, 151.2093]} // Sydney
        zoom={11} 
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {SUBURBS.map(suburb => (
          <Marker 
            key={suburb.name} 
            position={suburb.coords as [number, number]} 
            icon={icon}
            eventHandlers={{
              click: () => handleMarkerClick(suburb.name, suburb.price)
            }}
          >
            <Popup>
              <div style={{ fontWeight: 'bold' }}>{suburb.name}</div>
              <div style={{ color: '#10b981', fontWeight: 600 }}>Avg: {suburb.price}</div>
              <div style={{ fontSize: '10px', marginTop: '4px', color: '#666' }}>Click to analyze & predict via AI</div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
