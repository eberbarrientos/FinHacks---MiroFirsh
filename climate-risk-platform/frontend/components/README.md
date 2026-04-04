# Dashboard Components - Phase 2

This directory contains the Phase 2 dashboard statistics and chart components for the Climate Risk Intelligence Platform.

## Components

### 1. PortfolioStatsRow

**File**: `PortfolioStatsRow.tsx`

**Purpose**: Displays key portfolio metrics in a hero statistics row with animated counters and glassmorphism styling.

**Features**:
- Animated counter effect (0 to final value over 1 second) using Framer Motion
- Glassmorphism styling with backdrop blur and thin borders
- Color-coded risk levels (cyan/teal for neutral, amber for medium, red for high)
- Responsive grid layout (1 column mobile, 2 columns tablet, 5 columns desktop)
- Smooth hover effects with glow animations

**Props**:
```typescript
interface PortfolioStatsRowProps {
  portfolioValue: number        // Total portfolio value in USD
  climateVar: number            // Climate Value at Risk in USD
  stressedDrawdown: number      // Stressed drawdown percentage
  topHotspot: string            // Name of top geographic hotspot
  topSectorRisk: string         // Name of top sector risk
  className?: string            // Optional additional CSS classes
}
```

**Requirements**: 8.1, 8.2, 13.2, 13.3, 13.4

---

### 2. IssuerRiskTable

**File**: `IssuerRiskTable.tsx`

**Purpose**: Displays issuer-level risk metrics in a sortable, filterable table with premium styling.

**Features**:
- Sortable columns (click header to sort ascending/descending/reset)
- Risk threshold filtering (All, Low 40+, High 70+)
- Color-coded risk scores with badges
- Hover effects on rows
- Staggered animation on load
- Responsive table layout

**Props**:
```typescript
interface IssuerRiskTableProps {
  data: IssuerRiskData[]        // Array of issuer risk data
  className?: string            // Optional additional CSS classes
}

interface IssuerRiskData {
  issuer_name: string           // Name of the issuer
  aggregated_loss: number       // Total aggregated loss in USD
  combined_score: number        // Combined risk score (0-100)
  holdings_count: number        // Number of holdings for this issuer
}
```

**Requirements**: 8.1

---

### 3. LossWaterfallChart

**File**: `LossWaterfallChart.tsx`

**Purpose**: Visualizes contribution to total loss by sector using a waterfall chart.

**Features**:
- Waterfall chart showing cumulative loss progression
- Color-coded bars based on contribution percentage:
  - Green: Low impact (<10%)
  - Amber: Medium impact (10-25%)
  - Red: High impact (>25%)
  - Cyan: Total
- Interactive tooltips with detailed metrics
- Dark mode color scheme
- Smooth animations on load
- Responsive chart sizing

**Props**:
```typescript
interface LossWaterfallChartProps {
  data: SectorLossData[]        // Array of sector loss data
  className?: string            // Optional additional CSS classes
}

interface SectorLossData {
  sector: string                // Sector name
  loss: number                  // Loss amount in USD
}
```

**Requirements**: 8.3

---

### 4. SectorHeatmap

**File**: `SectorHeatmap.tsx`

**Purpose**: Displays risk intensity across sectors using a color gradient heatmap.

**Features**:
- Grid layout with color-coded risk cells
- Color gradient from green (low risk) to red (high risk)
- Interactive hover tooltips with detailed sector information
- Risk score badges and visual progress bars
- Scale legend showing risk gradient
- Responsive grid (2 columns mobile, 3 tablet, 4 desktop)
- Smooth hover animations and scale effects

**Props**:
```typescript
interface SectorHeatmapProps {
  data: SectorRiskData[]        // Array of sector risk data
  className?: string            // Optional additional CSS classes
}

interface SectorRiskData {
  sector: string                // Sector name
  risk_score: number            // Risk score (0-100)
  holdings_count: number        // Number of holdings in sector
  total_exposure: number        // Total exposure in USD
}
```

**Requirements**: 8.4

---

## Design System

### Colors

**Risk Levels**:
- Low (0-40): Emerald/Green (`#10b981`, `#22c55e`)
- Medium (40-70): Amber/Yellow (`#f59e0b`, `#eab308`)
- High (70-100): Red/Orange (`#ef4444`, `#f97316`)
- Neutral: Cyan/Teal (`#06b6d4`, `#14b8a6`)

**Background**:
- Dark slate tones (`slate-800`, `slate-900`, `slate-950`)
- Glassmorphism: `bg-slate-800/40 backdrop-blur-xl`
- Borders: `border-slate-700/50`

### Animations

All components use Framer Motion for smooth animations:
- **Duration**: Maximum 300ms for state changes (Requirement 13.4)
- **Counter animations**: 1 second duration (Requirement 8.2)
- **Stagger delays**: 30-50ms between items
- **Hover effects**: Scale, glow, and color transitions

### Typography

- **Headers**: `text-xl font-bold text-slate-100`
- **Labels**: `text-sm text-slate-400`
- **Values**: `text-2xl font-bold` with risk-based colors
- **Monospace numbers**: `font-mono` for financial values

### Layout

- **Border radius**: `rounded-2xl` (2xl = 1rem)
- **Padding**: `p-6` for cards
- **Gaps**: `gap-4` for grids, `gap-6` for sections
- **Shadows**: `shadow-lg hover:shadow-xl`

---

## Usage Example

```tsx
import {
  PortfolioStatsRow,
  IssuerRiskTable,
  LossWaterfallChart,
  SectorHeatmap,
} from '@/components'

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <PortfolioStatsRow
        portfolioValue={250000000}
        climateVar={18750000}
        stressedDrawdown={7.5}
        topHotspot="Texas Gulf Coast"
        topSectorRisk="Utilities"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LossWaterfallChart data={sectorLossData} />
        <SectorHeatmap data={sectorRiskData} />
      </div>

      <IssuerRiskTable data={issuerData} />
    </div>
  )
}
```

---

## Demo

A demo page is available at `/dashboard` showing all components with sample data.

To run the demo:
```bash
npm run dev
```

Then navigate to `http://localhost:3000/dashboard`

---

## Dependencies

- **React 18.3+**: Core framework
- **Next.js 15+**: App Router
- **Framer Motion 11+**: Animations
- **Recharts 2.12+**: Charts
- **Tailwind CSS 3.4+**: Styling
- **Lucide React**: Icons

---

## Testing

All components are fully typed with TypeScript and follow the design system specifications.

To check for type errors:
```bash
npx tsc --noEmit
```

---

## Future Enhancements

- Add data export functionality (CSV, PDF)
- Implement real-time data updates
- Add comparison mode for multiple scenarios
- Add accessibility improvements (ARIA labels, keyboard navigation)
- Add unit tests with Vitest and React Testing Library
