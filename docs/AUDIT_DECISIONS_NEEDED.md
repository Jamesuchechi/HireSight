# AUDIT SUMMARY - DECISION NEEDED

## 🔴 CRITICAL ISSUE

**Missing File:** `/templates/interviews/privacy/consent_modal.html`
- **Referenced in:** `apps/interviews/privacy_views.py:65`
- **Impact:** ConsentModalView will throw TemplateDoesNotExist error
- **Fix:** Create file OR redirect to `practice/consent_modal.html`

---

## 🟡 HIGH PRIORITY ISSUES

### Issue #1: Orphaned Template - practice_history_dashboard.html
- **Status:** Created in Phase 1, but URL not accessible
- **View:** PracticeHistoryDashboardView exists
- **URL:** `/interviews/practice/history/` IS registered in urls.py
- **Current:** Can't access from UI
- **Content:** 350+ lines with Chart.js, badges, streaks (advanced dashboard)
- **Current Dashboard:** `practice_dashboard.html` (basic list)
- **Question:** Should this REPLACE the basic dashboard?

### Issue #2: Orphaned Template - session_controls.html
- **Status:** Created in Phase 1, but never rendered
- **Purpose:** Pause/resume/skip/exit session controls  
- **Rendered By:** No view uses it
- **Question:** Should this be removed or wired to a view?

### Issue #3: DUPLICATE Practice Setup Flows
- **Flow A (OLD):** `/practice/new/` → `create_practice_session.html` (basic form)
- **Flow B (NEW):** `/practice/setup/` → `practice_setup.html` (modern modal UX)
- **Question:** Should we keep both or deprecate the old one?

### Issue #4: Possibly Orphaned Python Files
- **ai.py** - Old AI module (check if ai_connector.py replaced it)
- **progress_tasks.py** - Purpose unclear

---

## ✅ WHAT'S WORKING WELL

- All interview management URLs/views/templates are properly wired
- All 9 forms are properly connected
- Privacy/consent system mostly complete (except template)
- New UX improvements (Phase 1) well-structured
- No critical import errors
- Admin interface updated

---

## YOUR DECISIONS NEEDED

### Decision #1: Missing Privacy Template
**Options:**
- A) Create new `/templates/interviews/privacy/consent_modal.html`
- B) Update `privacy_views.py` to use `/templates/interviews/practice/consent_modal.html` (reuse existing)

**Recommendation:** Option B (simpler, avoids duplication)

### Decision #2: Practice History Dashboard
**Current:** PracticeDashboardView renders `practice_dashboard.html` (basic)
**Alternative:** PracticeHistoryDashboardView renders `practice_history_dashboard.html` (advanced with charts)

**Your Choice:**
- [ ] Replace basic dashboard with advanced one
- [ ] Keep both (serve different purposes?)
- [ ] Remove advanced one (it's dead code)

### Decision #3: Setup Flow
**Old:** `/interviews/practice/new/` - basic form
**New:** `/interviews/practice/setup/` - modern UX modal

**Your Choice:**
- [ ] Keep both (support migration period)
- [ ] Deprecate old flow (remove after update links)
- [ ] Remove old immediately

### Decision #4: Session Controls Template
**Status:** Created but unused

**Your Choice:**
- [ ] This is intentional (AJAX-only)
- [ ] This should be wired to a view
- [ ] This should be removed (dead code)

---

## RECOMMENDED ACTIONS (Please Confirm)

1. ✅ **Fix Missing Template:** Redirect privacy_views to use practice/consent_modal.html
2. ✅ **Activate Advanced Dashboard:** Wire URL to PracticeHistoryDashboardView, make it the default
3. ✅ **Consolidate Setup:** Deprecate old setup flow, keep new UX flow only
4. ✅ **Remove Dead Code:** Delete session_controls.html and related code
5. ✅ **Verify:** Check ai.py and progress_tasks.py for actual use

---

## FILES AFFECTED

### Will Modify (2)
- `apps/interviews/privacy_views.py` (1 line change)
- `apps/interviews/urls.py` (remove old route)

### Will Create (0-1)
- Depends on your choice for Issue #1

### Will Delete (2-4)
- `templates/interviews/practice/create_practice_session.html` (after migration)
- `templates/interviews/practice/session_controls.html` (if unused)
- `apps/interviews/ai.py` (if orphaned)
- `apps/interviews/progress_tasks.py` (if orphaned)

---

## QUESTIONS FOR YOU

Please answer these 4 questions to proceed:

**Q1:** For the missing `/templates/interviews/privacy/consent_modal.html`:
- [ ] Create new file
- [ ] Reuse practice/consent_modal.html

**Q2:** For practice_history_dashboard.html:
- [ ] Replace current dashboard with advanced version
- [ ] Keep both separate
- [ ] Delete the advanced version

**Q3:** For setup flow (new vs old):
- [ ] Keep both during transition period
- [ ] Remove old flow immediately
- [ ] Keep only old flow (current is fine)

**Q4:** For session_controls.html:
- [ ] This is needed (wire it)
- [ ] Dead code (remove it)
- [ ] Not sure (skip for now)

Once you answer these, I'll proceed with:
1. Showing exact changes before applying
2. Applying all changes
3. Running full verification
4. Providing final summary
