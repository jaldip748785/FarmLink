# FarmLink Repair Plan

## PHASE 2: REPAIR PRIORITIES

### P0 - Critical
1. **Order Management:** Implement API endpoints and UI buttons for Farmer to update Order Status ("Pending Payment" -> "Processing" -> "Completed" -> "Cancelled"). Allow Buyer to Cancel pending orders.
2. **Forgot Password:** Implement password reset logic (either email link or basic OTP flow stored in DB).
3. **Cart Integration:** Add a dynamic cart badge to the navbar.

### P1 - Core FarmLink
4. **Product Reviews:** 
    - Create `Review` model (`id, product_id, buyer_id, rating, comment, created_at`).
    - Create `/api/reviews` endpoints (or normal form routes).
    - Add review section to `buyer/product_details.html`.
    - Ensure only buyers who ordered can review.
5. **Buyer/Seller Contact Chat:**
    - Create `Message` model (`id, sender_id, receiver_id, content, created_at, is_read`).
    - Add UI to `contact_farmer.html` for true internal messaging.
    - Create inbox for messages.

### P2 - Supporting Features
6. **Home Page Data:** Replace hardcoded products in `templates/index.html` with a DB query fetching the latest 3 active products.
7. **Favourites / Wishlist:**
    - Create `Favourite` model (`id, user_id, product_id`).
    - Add 'Heart' icon to products.
    - Implement `/buyer/favourites` view.
8. **Weather API:** Integrate a free Weather API or create a placeholder API component that pulls real weather based on user location.
9. **Contact Us Form:** Create contact form that stores inquiries in the database.

### P3 - UI Improvements
10. **Notification & Cart Badges:** Ensure they accurately display real-time counts from DB.

---
**Methodology:**
For every repaired feature:
`IMPLEMENT -> TEST -> REGRESSION TEST -> DOCUMENT`
All fixes will be logged in `/docs/repair-log.md`.
