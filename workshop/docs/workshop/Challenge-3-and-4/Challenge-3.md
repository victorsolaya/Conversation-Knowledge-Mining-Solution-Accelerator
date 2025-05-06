# Workshop Challenge: Changing the Logo in the App

One of the easiest and most fun changes you can make to the app is updating the logo! Follow these step-by-step instructions to replace the current logo with your own.

---

## **Step 1: Prepare Your New Logo**
1. Create or use a new logo (e.g contosoImg logo) in `src/assets/`.
2. Save the logo as an image file (e.g., `logo.png`).
3. Ensure the image has a reasonable size (e.g., 100x100 pixels) for better display.
4. Place the logo file in the following folder:
    `src/assets/`

---


## Step 2: Update the Logo Component

1. Open the `App.tsx` file located at:  
   `src/App/src/App.tsx`

2. Import your logo image at the top of the file. It should look like this:

   ```tsx
   import AppLogo from "./assets/contosoimg/ContosoImg.png";

3. Locate the current logo in the JSX (around line 311).

4. Comment out the old logo line and replace it with:
      <img src={AppLogo} alt="Logo" style={{ width: '30px' }} />

---


## Step 3: Run the App

1. Open a terminal or command prompt.

2. Navigate to the project directory where start.cmd is located:
   `cd src/`

3. Run the following command: 
   `./start.cmd`

4. Two terminal windows will open — one for the backend and one for the frontend.
Once the app starts, you should see your new logo in action!

