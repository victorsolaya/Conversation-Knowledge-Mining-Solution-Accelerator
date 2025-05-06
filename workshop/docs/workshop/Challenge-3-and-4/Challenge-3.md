# Workshop Challenge: Changing the Logo in the App

One of the easiest and most fun changes you can make to the app is updating the logo! Follow these step-by-step instructions to replace the current logo with your own.

---

## **Step 1: Prepare Your New Logo**
1. Create or find the logo you want to use.
2. Save the logo as an image file (e.g., `logo.png`).
3. Ensure the image has a reasonable size (e.g., 100x100 pixels) for better display.

---

## **Step 2: Add the Logo to the Project**
1. Navigate to the `src/components/Svg` folder in your project directory.
2. Replace the existing logo file or add your new logo file to this folder.
   - Example: Save your new logo as `NewLogo.svg` or `newLogo.png`.

---

## **Step 3: Update the Logo Component**
1. Open the `App.tsx` component file which is located in `src/App/src/App.tsx`:
   - import your logo and include the correct file path. it will look like this : 
      `import { AppLogo } from "./components/Svg/Svg";`

2. Locate the current logo implementation. It might look like this:

```tsx
<div className="header-left-section">
          <AppLogo />
          <Subtitle2>
            Woodgrove <Body2 style={{ gap: "10px" }}>| Call Analysis</Body2>
          </Subtitle2>
        </div>
```

4. Save your files

5. Open a terminal or command prompt.

6. Navigate to the project directory where start.cmd is located:`src/ ` and run `./start.cmd`

5. Open a web browser and navigate to the local development server (http://127.0.0.1:5000).
Verify that the new logo is displayed in the application.
