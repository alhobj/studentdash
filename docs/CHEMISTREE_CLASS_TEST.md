# Test the existing class workflow with Chemistree

Use Studentdash **work** and Chemistree **main**. No full branch merge is needed.
Keep your current `data` directory; the connector uses the classes you already saved.

1. Update Studentdash's `work` branch. Close the old teacher server and run
   **start-assessment-import.bat**. Open `http://127.0.0.1:5000/classes`.
2. Open your existing class. Continue using Import assessment → Copy prompt →
   ChatGPT with test paper → paste metadata JSON → Preview → Import assessment.
   Skip this if the assessment is already saved. Paste/save question scores normally.
3. Prepare the viewer once: update Chemistree `main`; in that project folder run
   `npm ci`, then `npm run build:local`. This creates `local-package`.
4. Back in the class, click **Export Studentdash + Chemistree**. Paste the full
   path to Chemistree's `local-package` and click **Load viewer / saved assignments**.
5. Review the directly assessed node for each question part. Exact reviewed links
   are reused when their stable IDs match. Existing broad section classifications
   cannot identify a single statement; choose one explicitly, or exclude that part.
   Assignments are saved in your private class, not in another mapping JSON file.
   One scored part contributes once, never its full marks to several nodes.
6. Choose one student and a new empty local folder. Click **Save assignments and
   export student folder**. Share only that individual folder through OneDrive.
   The master workbook, class database and other students are excluded.
7. On the student computer, download/keep the whole folder locally (OneDrive:
   **Always keep on this device**). Open **Start Studentdash.cmd**. This opens the
   Studentdash report and Chemistree; keep the launcher window open. No Node or
   Python installation is needed on the student computer for the Windows viewer.
8. Confirm the Studentdash totals. A node with graded 4/5 evidence should show
   **Results 4/5**: click its ring to see test/question evidence. Absent, exempt,
   missing and pending parts are excluded from the ring; graded zeros are included.
9. Set confidence on a node. In Studentdash change a score and save it, then export
   that student again **to the same folder**. After OneDrive sync, Chemistree reloads
   results automatically (or click Reload results); reopen the Studentdash report
   to see its fresh snapshot. Confidence should remain unchanged.

Repeat export for each learner; the page remembers each learner's destination.
Do not replace a learner's package.json or export to a different folder to update
results. Confidence belongs to the student's same browser/profile at
`http://127.0.0.1:8765`, separated by package ID. Export confidence for a backup;
OneDrive syncs results, not browser confidence. Only one viewer runs on that port
at a time. If school policy blocks the Windows launcher, test that restriction
before distributing folders; the script never bypasses execution policy.

Node assignments and export settings use the normal class version checks and
backups. This connector does not migrate saved classes, replace classifications,
or change the separate assessment-level confidence ratings.
