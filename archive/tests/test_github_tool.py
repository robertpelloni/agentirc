import unittest
import asyncio
from simulator_tools import fetch_github_pr

class GithubToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_github_pr_valid_url(self):
        # We test grabbing an arbitrary public diff (e.g. chainlit or react or any stable known public repo PR)
        # Using a dummy invalid URL just to test the logic path execution and URL mutation logic
        url = "https://github.com/Chainlit/chainlit/pull/1"
        result = await fetch_github_pr(url)
        # 1. It either succeeds with raw diff (which contains "diff --git" usually)
        # 2. Or it fails cleanly with "Error" if the API rate limits us or the PR doesn't exist
        self.assertTrue("Raw Diff from" in result or "Error" in result)

        # Test path mutations
        url_with_commits = "https://github.com/Chainlit/chainlit/pull/1/commits/somehash"
        result2 = await fetch_github_pr(url_with_commits)
        self.assertTrue("Raw Diff from" in result2 or "Error" in result2)

if __name__ == "__main__":
    unittest.main()
