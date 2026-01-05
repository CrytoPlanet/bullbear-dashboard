# GitHub Pages Environment Setup Guide

## Enable Feat Branch Deployment for Testing

To test deployments on feat branches before creating a PR, you need to modify the GitHub Pages environment protection rules.

### Steps:

1. **Go to Repository Settings**
   - Navigate to your repository on GitHub
   - Click on **Settings** tab

2. **Access Environments**
   - In the left sidebar, click on **Environments**
   - Click on **github-pages** environment

3. **Modify Deployment Branches**
   - Scroll down to **Deployment branches** section
   - Select **Selected branches** (instead of "Protected branches only")
   - Click **Add branch** button
   - Enter `feat/**` pattern to allow all feat branches
   - Or select **All branches** to allow any branch to deploy
   - Click **Save protection rules**

4. **Verify**
   - After saving, push to your feat branch
   - The deployment workflow should now run successfully
   - Check the Actions tab to see the deployment progress

### Alternative: Use Local Testing

If you prefer not to modify environment rules, you can test locally:

```bash
# Install dependencies
cd frontend
pnpm install

# Build the project
pnpm run build

# Preview the build
pnpm preview
# Or use a static server
# npx serve dist
```

### Important Notes

- **Main branch protection**: The main branch will still be protected and require PR reviews
- **Feat branch deployments**: Will overwrite the main branch deployment temporarily
- **Testing workflow**: After testing on feat branch, merge to main for production deployment

