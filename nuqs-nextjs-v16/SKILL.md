---
name: nuqs-nextjs-v16
description: Implement, review, or refactor typed URL query state with nuqs v2 in Next.js 16 App Router projects, including shared parsers, server parsing, client controls, query links, canonical URLs, and testing.
---

# nuqs + Next.js 16

Treat the URL as a typed contract shared by client controls, server rendering, and links. Prefer the smallest arrangement the route needs: shared parsers, a hook, and server parsing only when server output depends on the query.

## Version and setup

Verified against official documentation and nuqs 2.10.1 on 2026-09-02. The [changelog](https://nuqs.dev/docs/changelog) lists 2.10.1; [nuqs v2 supports Next.js >=14.2](https://nuqs.dev/docs/installation), including Next.js 16.

Inspect the project's installed versions, lockfile, adapter, and Next.js configuration first. Use its configured package manager and preserve compatible dependencies. For a new installation targeting this skill, install `nuqs@^2`. Check feature availability before copying examples into older v2 projects:

- `createLoader`: 2.3+.
- Strict loaders, `limitUrlUpdates`, `debounce`, and adapter `defaultOptions`: 2.5+.
- `processUrlSearchParams`: 2.6+.
- `parseAsNativeArrayOf`: 2.7+ (used below).

Recheck the docs for a different nuqs or Next.js major. Do not upgrade a project just to match the verification version.

Use URL state for shareable filters, sorting, pagination, tabs, and navigation-like dialogs. Keep secrets, private data, large payloads, and transient state that does not belong in navigation out of the URL.

Wrap the app in the [App Router adapter](https://nuqs.dev/docs/adapters#app-router). Keep an existing adapter if already configured.

```tsx
// src/app/layout.tsx
import { NuqsAdapter } from 'nuqs/adapters/next/app'
import type { ReactNode } from 'react'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body><NuqsAdapter>{children}</NuqsAdapter></body>
    </html>
  )
}
```

Use `nuqs/adapters/next` when a shared adapter must serve both App and Pages routers. A pure App Router app can use the smaller dedicated import above.

## Shared parser contract

Colocate `search-params.ts` with the owning route or feature. Import shared parsers and utilities from `nuqs/server`; despite its name, this entry point is usable by both client and server code and avoids the client directive on `nuqs`. Import hooks from `nuqs` in Client Components.

```ts
// src/app/products/search-params.ts
import {
  createLoader,
  createSerializer,
  parseAsIndex,
  parseAsInteger,
  parseAsNativeArrayOf,
  parseAsString,
  parseAsStringLiteral,
  type inferParserType,
} from 'nuqs/server'

const sortValues = ['newest', 'price-asc', 'price-desc'] as const

export const productSearchParams = {
  q: parseAsString.withDefault(''),
  page: parseAsIndex.withDefault(0),
  sort: parseAsStringLiteral(sortValues).withDefault('newest'),
  brandIds: parseAsNativeArrayOf(parseAsString),
  minPrice: parseAsInteger,
  maxPrice: parseAsInteger,
}

export type ProductSearchParams = inferParserType<typeof productSearchParams>
export const loadProductSearchParams = createLoader(productSearchParams)
export const serializeProductSearchParams = createSerializer(productSearchParams)
```

Use `inferParserType` for props and service inputs instead of duplicating the contract. Defaults remove nullability; here `minPrice` and `maxPrice` remain `number | null`. Keep one consistent parser/default definition per URL key across mounted hooks; their state synchronizes by key.

### Parser and default semantics

- Missing or unparseable values normally become `null`, or the parser's default. Reading a fallback does not rewrite an invalid URL.
- `.withDefault(...)` supplies state without eagerly adding a query key. In v2, `clearOnDefault` defaults to `true`: explicitly setting the default removes the key. Use `.withOptions({ clearOnDefault: false })` when links must retain an explicit default. Setting `null` always removes the key and restores its default in state.
- `parseAsIndex` offsets parsing by -1 and serialization by +1. With the contract above, `?page=3` means index `2`; setting index `0` removes `page`. Writing `?page=1` requires `clearOnDefault: false`. It does not validate nonnegative indexes.
- `parseAsNativeArrayOf` uses repeated keys (`?brandIds=bmw&brandIds=audi`) and defaults to `[]`. `parseAsArrayOf` uses a separator within one value; choose deliberately and preserve the existing URL format.
- For dates, distinguish `parseAsIsoDate` (UTC midnight), `parseAsIsoDateTime`, and `parseAsTimestamp`. Avoid interpreting UTC date-only values as local midnight.
- For structured JSON, use `parseAsJson` with a synchronous validator or supported Standard Schema, not a type assertion. Check the installed version for the schema overload.

Sources: [basic usage](https://nuqs.dev/docs/basic-usage), [built-in parsers](https://nuqs.dev/docs/parsers/built-in), [utilities](https://nuqs.dev/docs/utilities).

### Short URL keys

Only abbreviate keys when it helps the product. If using `urlKeys`, share the mapping across **every** consumer; mapping only the server cache makes hooks and links disagree.

```ts
// Alternative wiring in search-params.ts, after the parser declaration:
import { createSearchParamsCache, type UrlKeys } from 'nuqs/server'

export const productUrlKeys = {
  minPrice: 'min',
  maxPrice: 'max',
  brandIds: 'b',
} satisfies UrlKeys<typeof productSearchParams>

// Replace the corresponding unmapped factories when enabling this mapping.
export const loadMappedProducts = createLoader(productSearchParams, { urlKeys: productUrlKeys })
export const serializeMappedProducts = createSerializer(productSearchParams, { urlKeys: productUrlKeys })
export const mappedProductsCache = createSearchParamsCache(productSearchParams, { urlKeys: productUrlKeys })
```

In the client, also pass `{ urlKeys: productUrlKeys }` to `useQueryStates(productSearchParams, ...)`. Mapping changes require considering existing shared links. See [key mapping](https://nuqs.dev/docs/batching#shorter-search-params-keys).

## Server parsing and rendering

Next.js 16 pages receive `searchParams` as a promise resolving to a plain record, including arrays for repeated keys. Use `Promise<SearchParams>` from `nuqs/server`, or Next's generated global `PageProps<'/products'>`. Layouts do not receive fresh `searchParams`; read them in pages or client hooks. See [page props](https://nextjs.org/docs/app/api-reference/file-conventions/page) and [useSearchParams](https://nextjs.org/docs/app/api-reference/functions/use-search-params).

Use a loader for page props and Route Handlers. Only add `createSearchParamsCache` if nested Server Components need access without props.

```tsx
// src/app/products/page.tsx
import { Suspense } from 'react'
import type { SearchParams } from 'nuqs/server'
import { loadProductSearchParams } from './search-params'
import { ProductFilters } from './product-filters'

type ProductsPageProps = { searchParams: Promise<SearchParams> }

export default function ProductsPage({ searchParams }: ProductsPageProps) {
  return (
    <main>
      <h1>Products</h1>
      <Suspense fallback={<p>Loading filters...</p>}>
        <ProductFilters />
      </Suspense>
      <Suspense fallback={<p>Loading products...</p>}>
        <ProductResults searchParams={searchParams} />
      </Suspense>
    </main>
  )
}

async function ProductResults({ searchParams }: ProductsPageProps) {
  const params = await loadProductSearchParams(searchParams)
  // Validate domain constraints, then fetch products with these typed values.
  return <p>Search: {params.q}; page: {params.page + 1}</p>
}
```

For a fully dynamic page without Cache Components, awaiting the loader in the page and passing parsed props is also valid. With `cacheComponents: true`, consume request-dependent values under Suspense to keep a static shell; a boundary returned after an `await` cannot cover that earlier suspension. Do not read request data inside `use cache`; resolve and validate query values outside, then pass them as arguments to cached functions. See [Cache Components](https://nextjs.org/docs/app/getting-started/caching) and [request data in use cache](https://nextjs.org/docs/messages/next-request-in-use-cache).

For nested server consumers, declare a cache from the same contract:

```ts
// src/app/products/search-params-cache.ts
import { createSearchParamsCache } from 'nuqs/server'
import { productSearchParams } from './search-params'

export const productSearchParamsCache = createSearchParamsCache(productSearchParams)
```

Await `productSearchParamsCache.parse(searchParams)` in the page or a query-dependent ancestor under Suspense **before rendering descendants** that call `.get('q')` or `.all()`. The cache lasts for the server render; it is neither persistent data caching nor client state. Client Components use the shared parsers with hooks. See [server-side usage](https://nuqs.dev/docs/server-side).

For statically rendered routes, nuqs hook consumers need a Suspense ancestor; development mode can hide a missing boundary that fails a production build. Keep hook usage in a small Client Component. Intentionally dynamic rendering can avoid this static-rendering requirement, so Suspense is not an unconditional requirement of every hook call. See [Next.js rendering behavior](https://nextjs.org/docs/app/api-reference/functions/use-search-params#behavior).

## Client updates

Use `useQueryState` for one key and `useQueryStates` for related keys. When filters change, reset pagination in the same update. This example assumes server-rendered results, hence `shallow: false`:

```tsx
// src/app/products/product-filters.tsx
'use client'

import { useTransition } from 'react'
import { debounce, useQueryStates } from 'nuqs'
import { productSearchParams } from './search-params'

export function ProductFilters() {
  const [isPending, startTransition] = useTransition()
  const [filters, setFilters] = useQueryStates(productSearchParams, {
    shallow: false,
    startTransition,
  })

  return (
    <label>
      Search products
      <input
        value={filters.q}
        onChange={(event) => {
          const q = event.currentTarget.value
          void setFilters({ q, page: 0 }, {
            limitUrlUpdates: q === '' ? undefined : debounce(300),
          })
        }}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            void setFilters({ q: event.currentTarget.value, page: 0 })
          }
        }}
      />
      {isPending ? <span role="status">Loading...</span> : null}
    </label>
  )
}
```

Defaults are client-only updates (`shallow: true`), history replacement, no scroll, and browser-adapted throttling. Set `shallow: false` when server results must refresh. Passing `startTransition` alone does not enable server updates; its pending state covers the transition, not the debounce wait.

Debounce URL/server writes while keeping input state immediate. Apply it to typing; clear and Enter can use normal scheduling, as above. To override a hook-level debounce, use `defaultRateLimit`. nuqs debouncing does **not** debounce client fetching driven by hook state: debounce the value supplied to that fetching layer separately. `throttle(ms)` instead produces periodic updates. Use `limitUrlUpdates`, not deprecated `throttleMs`.

Use `history: 'push'` for navigation-like tabs or dialogs whose changes should be traversable with Back. Avoid pushing every keystroke. Set `scroll: true` for navigation that should scroll to the top. See [options](https://nuqs.dev/docs/options).

`useQueryStates` setters accept partial objects, functional updates, or `null` to clear all managed keys while preserving unrelated query keys. For example, `void setFilters(previous => ({ page: previous.page + 1 }))`. Options resolve from call > parser > hook > adapter defaults. Updates batch before URL writes; the setter's promise resolves to the flushed `URLSearchParams`, not completion of server data fetching. See [batching](https://nuqs.dev/docs/batching).

## Route Handlers and validation

Loaders accept `Request`, `URL`, `URLSearchParams`, query strings, records, and promises of those inputs. Preserve repeated keys by passing the original input instead of flattening it with `Object.fromEntries`.

```ts
// src/app/api/products/route.ts
import { NextResponse } from 'next/server'
import { loadProductSearchParams, type ProductSearchParams } from '@/app/products/search-params'

export function GET(request: Request) {
  let params: ProductSearchParams
  try {
    params = loadProductSearchParams(request, { strict: true })
  } catch {
    return NextResponse.json({ error: 'Invalid query parameters' }, { status: 400 })
  }

  if (!Number.isSafeInteger(params.page) || params.page < 0) {
    return NextResponse.json({ error: 'Invalid page' }, { status: 400 })
  }

  return NextResponse.json({ q: params.q, page: params.page, sort: params.sort })
}
```

Strict mode throws when a present value fails its parser; missing values still use defaults or `null`. Catch parse errors at an API boundary when they should become a 400. Keep unrelated fetch failures outside that catch.

Strict mode is not business validation or necessarily strict lexical validation. For example, `parseAsInteger` uses integer parsing, which can accept a numeric prefix; arrays can discard invalid entries. Check ranges, safe integers, relationships such as `minPrice <= maxPrice`, and permissions separately. If malformed numeric syntax or every invalid array entry must be rejected, implement that policy in a shared custom parser. Server normalization alone does not update client URL state. See [strict loaders](https://nuqs.dev/docs/server-side#strict-mode).

For [custom parsers](https://nuqs.dev/docs/parsers/making-your-own), use `createParser` with pure `parse` and `serialize`; return `null` for invalid input. Provide `eq` for objects/arrays whose semantic equality differs from reference equality. Keep the serialized representation sufficient to reconstruct the intended state; lossy serialization can change values on reload. Put reusable validation in the parser where appropriate, and retain authorization at the service boundary.

## Links and canonical URLs

Use the shared serializer for query links. A bare pathname starts fresh; a base containing the current query preserves keys you do not update. Omitted/`undefined` values leave base keys untouched; `null` removes them. Defaults use the same clearing behavior as hooks.

```tsx
// src/app/products/product-sort-links.tsx
import Link from 'next/link'
import { serializeProductSearchParams } from './search-params'

export function ProductSortLinks() {
  return (
    <nav aria-label="Product sort">
      <Link href={serializeProductSearchParams('/products', { sort: 'newest', page: 0 })}>
        Newest
      </Link>
      <Link href={serializeProductSearchParams('/products', { sort: 'price-asc', page: 0 })}>
        Cheapest
      </Link>
    </nav>
  )
}
```

These links intentionally start fresh. To preserve filters, pass a base with the current query or include the other typed filter values. For example, `serializeProductSearchParams('/products?q=oil&page=3', { sort: 'price-asc', page: 0 })` retains `q` and clears `page`. See [serializers](https://nuqs.dev/docs/utilities).

For local UI query state, set `alternates.canonical` to the query-free page URL. When parameters identify indexable content, generate the canonical with a loader and serializer, including only those content-defining keys. Start from a clean pathname so tracking parameters cannot leak into it. Configure the site's real `metadataBase` for relative canonical paths, or use an absolute canonical URL. Only add `processUrlSearchParams` (to both adapter and serializer) if consistent ordering or normalization is needed. See [nuqs SEO](https://nuqs.dev/docs/seo) and [Next.js metadataBase](https://nextjs.org/docs/app/api-reference/functions/generate-metadata#metadatabase).

## Focused verification

Use the project's existing type-check/build commands when an implementation changes rendering or imports. A development render alone does not prove static build compatibility. For component tests, use the nuqs testing adapter instead of mocking router internals.

```tsx
// src/app/products/product-filters.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { withNuqsTestingAdapter, type OnUrlUpdateFunction } from 'nuqs/adapters/testing'
import { expect, it, vi } from 'vitest'
import { ProductFilters } from './product-filters'

it('resets pagination when searching and preserves unrelated keys', async () => {
  const user = userEvent.setup()
  const onUrlUpdate = vi.fn<OnUrlUpdateFunction>()
  render(<ProductFilters />, {
    wrapper: withNuqsTestingAdapter({
      searchParams: '?q=oil&page=3&utm_source=test',
      onUrlUpdate,
    }),
  })

  await user.type(screen.getByRole('textbox', { name: 'Search products' }), ' filter')

  await waitFor(() => {
    const event = onUrlUpdate.mock.lastCall?.[0]
    expect(event?.searchParams.get('q')).toBe('oil filter')
    expect(event?.searchParams.has('page')).toBe(false)
    expect(event?.searchParams.get('utm_source')).toBe('test')
    expect(event?.options.shallow).toBe(false)
  })
})
```

This assumes a DOM test environment and modern Vitest. The adapter disables rate limiting by default: this verifies update semantics, not debounce timing. Use `rateLimitFactor: 1` with controlled timers for an actual debounce test. Use `hasMemory: true` when successive interactions must build on earlier URL updates. The adapter does not reproduce App Router server navigation or browser history.

Test domain-specific parsing/default/clearing behavior when it matters. For custom parsers, `nuqs/testing` provides `isParserBijective`, `testParseThenSerialize`, and `testSerializeThenParse`; test canonical round trips and intentional normalization separately. nuqs v2 is ESM-only; consult the [testing docs](https://nuqs.dev/docs/testing) if an existing Jest setup has module-loading errors.
