# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design for PawPal+ included four classes: Owner, Pet, CareTask, and DailyPlanner. The Owner stores the user’s info and preferences, the Pet stores pet details, the CareTask represents tasks like feeding or walking, and the DailyPlanner creates the daily schedule based on time, priority, and pet needs. Overall, each class has a clear role in organizing data and handling scheduling

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

## b. Design changes

Yes, my design changed during implementation.

Here are the main updates I made:

1. **Priority became an enum instead of a string.**  
   At first, priority was just text like “low,” “medium,” or “high.” I changed it to a `Priority` enum so invalid values can be caught right away.

2. **Preferences became their own dataclass.**  
   Instead of storing preferences in a generic dictionary, I created a `Preferences` dataclass. This made the data clearer and easier for the scheduler to use.

3. **ScheduledTask got an `end_time` field.**  
   Originally, it only stored the start time. I added `end_time` so each scheduled task is complete on its own and does not need extra calculations later.

4. **I added helper methods for time conversion.**  
   Since the scheduler needs to compare and calculate times, I created shared helper methods to handle time parsing instead of repeating that logic in multiple places.

5. **Task management was centralized.**  
   I made the `Owner` task-adding method private and used `PawPalApp` as the main public place to add or remove tasks. This made the design cleaner and easier for the UI to use.

6. **The plan now resets before rebuilding.**  
   I added a reset at the start of `build_plan` so generating a new plan does not accidentally duplicate old tasks.

7. **Pet behavior became more meaningful.**  
   I added `Pet.requires_outdoor_tasks()` so the app can make simple species-based decisions, such as not scheduling walks for cats.

Overall, these changes made the design safer, clearer, and easier to maintain.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler uses **priority-first, first-fit packing**: it sorts optional tasks from highest to lowest priority and slots each one in as long as it fits within the owner's available time budget. It does not try every possible ordering to find the globally optimal schedule.

This means a high-priority 60-minute task near the top of the list could block several shorter medium-priority tasks that would have collectively fit, even though dropping the long task and keeping the shorter ones might actually be a better plan for the owner.

For example, if 90 minutes remain and the next task is a 90-minute bath, the scheduler takes it — leaving nothing for the three 20-minute tasks that follow. A smarter algorithm (like knapsack or branch-and-bound) could find the arrangement that maximizes total priority-weighted minutes, but those approaches are significantly more complex to implement and harder to explain to a non-technical user.

The tradeoff is reasonable here because PawPal+ is a personal daily planner, not a logistics optimizer. Pet owners generally have a clear sense of what matters most, and a schedule that always does the highest-priority task first is easy to understand and trust. Predictability and transparency matter more in this scenario than squeezing out the last few minutes of theoretical efficiency.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

One important thing I learned from this project is that you should always review AI-generated work carefully and back it up with tests. Even if the code looks correct at first glance, it can still contain logic errors or miss important edge cases. Running both automated tests and manual checks is essential to make sure the program works accurately and as intended.
