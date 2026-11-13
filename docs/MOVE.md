# Move into the new repository

1. Create an empty private GitHub repository named **ArborSynapse**.
2. Download the **ArborSynapse branch** of `alhobj/studentdash` as a ZIP and extract it.
   This gets the small current folder without the old repositories' Git history.
3. In that extracted folder:

   ```sh
   git init -b main
   git add .
   git commit -m "Start ArborSynapse"
   git remote add origin https://github.com/alhobj/ArborSynapse.git
   git push -u origin main
   ```

4. Open Start.cmd. Copy your backed-up `data` folder only for local teacher use.
5. Configure Atlas using ATLAS.md. Future pushes update its test site automatically.

The original Studentdash `work` and Chemistree `main` remain available.
