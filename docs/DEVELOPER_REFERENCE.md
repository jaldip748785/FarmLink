# 🎨 FarmLink UI - Developer Reference Guide

## Quick Start for Developers

This guide helps you maintain and extend the FarmLink UI using the modern design system.

---

## 📦 CSS Files Structure

### 1. **style.css** - Main Design System
Contains:
- Global styles and typography
- Color variables
- Navigation styling
- Cards and buttons
- Responsive design

### 2. **forms.css** - Form Components
Contains:
- Form controls styling
- Input fields
- Labels and help text
- Validation states
- File uploads

### 3. **components.css** - Reusable Components
Contains:
- Cards and containers
- Badges and status indicators
- Avatars
- Utilities
- Loading states
- Modals and tooltips

---

## 🎨 Using CSS Custom Properties

### Primary Colors
```css
--primary: #22c55e;        /* Main green */
--primary-dark: #16a34a;   /* Dark green */
--primary-light: #86efac;  /* Light green */
```

### Neutral Colors
```css
--text-dark: #1e293b;      /* Main text */
--text-muted: #64748b;     /* Secondary text */
--border-color: #e2e8f0;   /* Borders */
--light: #f8fafc;          /* Light background */
--dark: #1e293b;           /* Dark background */
```

### Status Colors
```css
--success: #22c55e;        /* Green */
--danger: #ef4444;         /* Red */
--warning: #eab308;        /* Yellow */
--info: #06b6d4;           /* Cyan */
```

### Shadows
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
--shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.12);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
```

---

## 🎛️ Creating New Components

### Button Styles
```html
<!-- Primary Button -->
<button class="btn btn-success">
    <i class="bi bi-plus"></i> Add New
</button>

<!-- Secondary Button -->
<button class="btn btn-secondary">Cancel</button>

<!-- Outline Button -->
<button class="btn btn-outline-success">Learn More</button>

<!-- Large Button -->
<button class="btn btn-success btn-lg">
    <i class="bi bi-arrow-right"></i> Continue
</button>
```

### Card Components
```html
<!-- Basic Card -->
<div class="card">
    <div class="card-body">
        <h5 class="card-title">Title</h5>
        <p class="card-text">Description</p>
    </div>
</div>

<!-- Card with Image -->
<div class="card product-card">
    <img src="..." class="card-img-top" alt="...">
    <div class="card-body">
        <h5 class="card-title">Product Name</h5>
        <p class="card-text">Description</p>
        <a href="#" class="btn btn-success">View Details</a>
    </div>
</div>

<!-- Stat Card -->
<div class="card stat-card">
    <div class="card-body">
        <i class="bi bi-box-seam display-4 text-success"></i>
        <h3 class="stat-card h3">15</h3>
        <p class="text-muted">Total Products</p>
    </div>
</div>
```

### Form Components
```html
<!-- Form Group -->
<div class="form-group">
    <label class="form-label">Product Name <span class="required">*</span></label>
    <input type="text" class="form-control" placeholder="Enter product name">
    <small class="form-text">Maximum 100 characters</small>
</div>

<!-- Form Select -->
<div class="form-group">
    <label class="form-label">Category</label>
    <select class="form-select">
        <option>Select a category</option>
        <option>Vegetables</option>
        <option>Fruits</option>
    </select>
</div>

<!-- Textarea -->
<div class="form-group">
    <label class="form-label">Description</label>
    <textarea class="form-control" rows="4" placeholder="Enter product description"></textarea>
</div>

<!-- Checkbox -->
<div class="form-check">
    <input class="form-check-input" type="checkbox" id="organic">
    <label class="form-check-label" for="organic">
        This is organic produce
    </label>
</div>
```

### Badges & Indicators
```html
<!-- Success Badge -->
<span class="badge bg-success">Active</span>

<!-- Warning Badge -->
<span class="badge bg-warning">Pending</span>

<!-- Error Badge -->
<span class="badge bg-danger">Error</span>

<!-- Status Badge -->
<div class="status-badge status-active">
    <span class="status-dot"></span>
    Active
</div>
```

### Info Boxes
```html
<!-- Success Info -->
<div class="info-box success">
    <i class="bi bi-check-circle"></i>
    <strong>Success!</strong> Your product has been added.
</div>

<!-- Error Info -->
<div class="info-box error">
    <i class="bi bi-exclamation-circle"></i>
    <strong>Error!</strong> Something went wrong.
</div>

<!-- Warning Info -->
<div class="info-box warning">
    <i class="bi bi-exclamation-triangle"></i>
    <strong>Warning!</strong> Please check your inputs.
</div>
```

---

## 📐 Grid Layouts

### Using Bootstrap Grid
```html
<!-- 2-column layout -->
<div class="row g-4">
    <div class="col-md-6">Half width</div>
    <div class="col-md-6">Half width</div>
</div>

<!-- 3-column layout -->
<div class="row g-4">
    <div class="col-md-4">One-third</div>
    <div class="col-md-4">One-third</div>
    <div class="col-md-4">One-third</div>
</div>

<!-- Responsive layout -->
<div class="row g-4">
    <div class="col-lg-4 col-md-6 col-sm-12">Product Card</div>
    <!-- More cards... -->
</div>
```

### Using CSS Grid
```html
<div class="grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;">
    <div class="card">Card 1</div>
    <div class="card">Card 2</div>
    <div class="card">Card 3</div>
</div>
```

---

## 🎯 Common Patterns

### Hero Section
```html
<section class="hero py-5">
    <div class="container">
        <h1 class="display-4 fw-bold mb-3">Welcome!</h1>
        <p class="fs-5 mb-4">Start your farming journey with FarmLink</p>
        <a href="#" class="btn btn-light btn-lg">Get Started</a>
    </div>
</section>
```

### Feature Section
```html
<section class="py-5">
    <div class="container">
        <h2 class="fw-bold mb-4">Key Features</h2>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card text-center p-4">
                    <i class="bi bi-lightning-fill display-4 text-success mb-3"></i>
                    <h5>Fast</h5>
                    <p class="text-muted">Quick and easy transactions</p>
                </div>
            </div>
            <!-- More features... -->
        </div>
    </div>
</section>
```

### Product Grid
```html
<div class="row g-4">
    {% for product in products %}
    <div class="col-lg-4 col-md-6">
        <div class="card h-100 product-card">
            <img src="..." class="card-img-top" alt="...">
            <div class="card-body">
                <h5 class="card-title">{{ product.name }}</h5>
                <p class="card-text text-muted">{{ product.description }}</p>
                <div class="product-price mb-2">
                    ₹<strong>{{ product.price }}</strong>
                    <span class="product-unit">/ {{ product.unit }}</span>
                </div>
                <a href="#" class="btn btn-success w-100">View Details</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

---

## 📱 Responsive Breakpoints

```css
/* Extra small (mobile) */
@media (max-width: 480px) {
    /* Mobile styles */
}

/* Small (mobile landscape) */
@media (max-width: 768px) {
    /* Tablet styles */
}

/* Medium (tablet) */
@media (min-width: 769px) {
    /* Desktop styles */
}

/* Large (desktop) */
@media (min-width: 1024px) {
    /* Large desktop styles */
}

/* Extra large */
@media (min-width: 1200px) {
    /* Extra large desktop */
}
```

---

## 🎭 Utility Classes

### Buttons
```html
<button class="btn btn-success">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-outline-success">Outline</button>
<button class="btn btn-light">Light</button>
<button class="btn btn-lg">Large</button>
<button class="btn btn-sm">Small</button>
```

### Text
```html
<p class="text-dark">Dark text</p>
<p class="text-muted">Muted text</p>
<p class="text-success">Success text</p>
<p class="fw-bold">Bold text</p>
<p class="text-center">Centered text</p>
```

### Spacing
```html
<div class="mb-4">Margin bottom</div>
<div class="mt-3">Margin top</div>
<div class="px-4">Padding left & right</div>
<div class="py-5">Padding top & bottom</div>
<div class="my-4">Margin top & bottom</div>
```

### Display
```html
<div class="d-flex">Flex container</div>
<div class="d-grid">Grid container</div>
<div class="d-none">Hidden</div>
<div class="d-block">Block display</div>
<div class="d-inline">Inline display</div>
```

### Sizing
```html
<div class="w-100">Full width</div>
<div class="h-100">Full height</div>
<div class="mw-100">Max width 100%</div>
```

---

## 🎨 Typography

### Headings
```html
<h1 class="display-4 fw-bold">Large title</h1>
<h2 class="display-5 fw-bold">Subtitle</h2>
<h3 class="fw-bold">Section heading</h3>
```

### Text Sizes
```html
<p class="fs-1">Extra large text</p>
<p class="fs-5">Regular text</p>
<p class="fs-6">Small text</p>
```

---

## 🔄 Transitions & Animations

### Using Predefined Animations
```css
/* Used automatically on hover */
.card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-xl);
}

.btn:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
}
```

### Adding Animations
```html
<div class="fade-in">Fades in on load</div>
<div class="slide-up">Slides up on load</div>
<div class="bounce">Bounces on load</div>
```

---

## 🚀 Performance Tips

1. **Use CSS Variables**: Makes updates easier and improves maintainability
2. **Minimize Repaints**: Use `transform` instead of `top/left`
3. **GPU Acceleration**: Add `will-change` for animated elements
4. **Mobile First**: Design for mobile, then enhance for desktop
5. **Lazy Load Images**: Use `loading="lazy"` attribute

---

## 🔍 Testing Checklist

When creating new pages or components:

- [ ] Works on mobile (320px)
- [ ] Works on tablet (768px)
- [ ] Works on desktop (1024px+)
- [ ] All buttons are clickable/touchable
- [ ] Forms are easy to fill
- [ ] Colors have good contrast
- [ ] Fonts are readable
- [ ] Hover states work
- [ ] Responsive images
- [ ] No layout shifts
- [ ] Fast load time
- [ ] Accessible to screen readers

---

## 📚 Resources

### CSS Variables Usage
```css
/* Define in :root */
:root {
    --primary: #22c55e;
}

/* Use anywhere */
.element {
    color: var(--primary);
}

/* Override in specific scope */
.dark-theme {
    --primary: #16a34a;
}
```

### Bootstrap Utilities
Most Bootstrap 5 classes work out of the box:
- `.container` - Responsive container
- `.row` / `.col-*` - Grid system
- `.d-flex` - Flexbox
- `.gap-*` - Gaps
- `.p-*` / `.m-*` - Padding/Margin
- `.text-*` - Text utilities
- `.bg-*` - Background colors

---

## 🎯 Best Practices

1. **Use Semantic HTML**: `<button>`, `<nav>`, `<section>`, etc.
2. **Mobile First**: Start with mobile, add desktop enhancements
3. **Accessibility**: Use ARIA labels, alt text, proper contrast
4. **Performance**: Optimize images, minimize CSS
5. **Consistency**: Follow the design system
6. **Documentation**: Comment complex code
7. **Testing**: Test on various devices

---

## 🐛 Troubleshooting

### Styles Not Applying?
1. Check CSS file is linked
2. Check selector specificity
3. Clear browser cache
4. Check for typos

### Layout Broken on Mobile?
1. Check viewport meta tag
2. Use responsive grid
3. Test on actual device
4. Check CSS media queries

### Performance Issues?
1. Minimize CSS files
2. Optimize images
3. Remove unused CSS
4. Enable gzip compression

---

**Last Updated**: August 2026
**Version**: 2.0 Design System
