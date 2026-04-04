# RecommendationsPanel Component

## Overview

The `RecommendationsPanel` component displays prioritized portfolio optimization recommendations with filtering, sorting, and interactive features. It implements Requirements 6.1 and 6.6 from the Climate Risk Intelligence Platform specification.

## Features

- **Priority Badges**: Color-coded badges (critical: red, high: amber, medium: yellow, low: green)
- **Type Filtering**: Filter recommendations by type (rebalance, diversify, hedge, watchlist, insurance_review)
- **Dual Sorting**: Sort by priority or potential impact
- **Glassmorphism Styling**: Premium dark mode design with blur effects
- **Interactive Cards**: Hover effects and click handlers
- **Summary Statistics**: Count breakdown by priority level
- **Affected Holdings**: Display count of holdings impacted by each recommendation
- **Potential Impact**: Show potential loss reduction in millions

## Usage

```tsx
import { RecommendationsPanel } from '@/components'
import { recommendationApi } from '@/lib/recommendation-api'

function DashboardPage() {
  const [recommendations, setRecommendations] = useState([])

  useEffect(() => {
    async function loadRecommendations() {
      const data = await recommendationApi.getRecommendations(
        portfolioId,
        scenarioId
      )
      setRecommendations(data)
    }
    loadRecommendations()
  }, [portfolioId, scenarioId])

  return (
    <RecommendationsPanel
      recommendations={recommendations}
      onRecommendationClick={(rec) => {
        console.log('Clicked recommendation:', rec)
        // Handle recommendation click (e.g., filter dashboard, show details)
      }}
    />
  )
}
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `recommendations` | `Recommendation[]` | Yes | Array of recommendation objects from the API |
| `className` | `string` | No | Additional CSS classes for the container |
| `onRecommendationClick` | `(rec: Recommendation) => void` | No | Callback when a recommendation card is clicked |

## Recommendation Type

```typescript
interface Recommendation {
  id: string
  portfolio_id: string
  scenario_id: string
  recommendation_type: 'rebalance' | 'diversify' | 'hedge' | 'watchlist' | 'insurance_review'
  priority: 'critical' | 'high' | 'medium' | 'low'
  message: string
  affected_holdings?: string[]
  potential_impact?: number
  created_at: string
}
```

## Recommendation Types

- **Rebalance**: Suggestions to reduce exposure to high-risk holdings (combined_score > 75)
- **Diversify**: Recommendations to reduce geographic or sector concentration
- **Hedge**: Hedging strategies for risk mitigation
- **Watchlist**: Issuers requiring enhanced monitoring (aggregated_loss > 5% of issuer value)
- **Insurance Review**: Holdings with high insurance dependency and significant expected losses

## Priority Levels

Priority is calculated based on portfolio impact percentage:
- **Critical**: >10% portfolio impact (red badge)
- **High**: 5-10% portfolio impact (amber badge)
- **Medium**: 2-5% portfolio impact (yellow badge)
- **Low**: <2% portfolio impact (green badge)

## Styling

The component uses:
- Glassmorphism effects with `backdrop-blur-xl`
- Dark mode color scheme with slate backgrounds
- Color-coded badges for priorities and types
- Smooth animations with Framer Motion
- Hover effects and transitions
- Responsive grid layout for summary statistics

## API Integration

The component works with the recommendation API:

```typescript
// Get recommendations (auto-generates if not exist)
const recommendations = await recommendationApi.getRecommendations(
  portfolioId,
  scenarioId
)

// Force regeneration
await recommendationApi.generateRecommendations(portfolioId, scenarioId)
```

## Accessibility

- Semantic HTML structure
- Keyboard navigation support
- Color contrast meets WCAG guidelines
- Screen reader friendly labels
- Focus indicators on interactive elements

## Performance

- Memoized filtering and sorting
- Staggered animations for smooth rendering
- Efficient re-renders with React hooks
- Optimized for lists up to 100+ recommendations
