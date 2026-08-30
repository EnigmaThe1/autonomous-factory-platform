package com.llmcouncil.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity {
    private static final String OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
    private static final String[] COUNCIL_MODELS = {
            "openai/gpt-5.1",
            "google/gemini-3-pro-preview",
            "anthropic/claude-sonnet-4.5",
            "x-ai/grok-4"
    };
    private static final String CHAIRMAN_MODEL = "google/gemini-3-pro-preview";
    private static final String TITLE_MODEL = "google/gemini-2.5-flash";

    private final ExecutorService executor = Executors.newFixedThreadPool(8);
    private SharedPreferences prefs;
    private EditText questionInput;
    private Button askButton, historyButton, settingsButton;
    private ProgressBar progress;
    private TextView statusView;
    private LinearLayout results;

    static class ModelResponse {
        final String model, response;
        ModelResponse(String model, String response) { this.model = model; this.response = response; }
    }

    static class RankingResponse {
        final String model, ranking;
        final List<String> parsed;
        RankingResponse(String model, String ranking, List<String> parsed) {
            this.model = model; this.ranking = ranking; this.parsed = parsed;
        }
    }

    static class AggregateRank {
        final String model;
        final double average;
        final int count;
        AggregateRank(String model, double average, int count) {
            this.model = model; this.average = average; this.count = count;
        }
    }

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("llm_council_mobile", Context.MODE_PRIVATE);
        buildUi();
        if (apiKey().isEmpty()) showApiKeyDialog(true);
    }

    @Override protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }

    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }
    private String apiKey() { return prefs.getString("openrouter_api_key", "").trim(); }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(12), dp(16), dp(12));
        root.setBackgroundColor(0xFFF7F7F8);

        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText("LLM Council"); title.setTextSize(24); title.setTypeface(null, 1); title.setTextColor(0xFF111111);
        bar.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        historyButton = new Button(this); historyButton.setText("History"); historyButton.setOnClickListener(v -> showHistory()); bar.addView(historyButton);
        settingsButton = new Button(this); settingsButton.setText("Settings"); settingsButton.setOnClickListener(v -> showSettings()); bar.addView(settingsButton);
        root.addView(bar);

        TextView desc = new TextView(this);
        desc.setText("Stage 1 answers · Stage 2 peer ranking · Stage 3 chairman synthesis");
        desc.setTextColor(0xFF555555); desc.setPadding(0, dp(5), 0, dp(10));
        root.addView(desc);

        questionInput = new EditText(this);
        questionInput.setHint("Ask the council anything…");
        questionInput.setMinLines(3); questionInput.setMaxLines(8); questionInput.setGravity(Gravity.TOP | Gravity.START);
        questionInput.setBackgroundColor(0xFFFFFFFF); questionInput.setPadding(dp(12), dp(12), dp(12), dp(12));
        root.addView(questionInput, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        askButton = new Button(this); askButton.setText("Ask LLM Council"); askButton.setOnClickListener(v -> runCouncil());
        LinearLayout.LayoutParams askLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT); askLp.topMargin = dp(8);
        root.addView(askButton, askLp);

        LinearLayout pRow = new LinearLayout(this); pRow.setOrientation(LinearLayout.HORIZONTAL); pRow.setGravity(Gravity.CENTER_VERTICAL); pRow.setPadding(0, dp(8), 0, dp(6));
        progress = new ProgressBar(this); progress.setVisibility(View.GONE); pRow.addView(progress, new LinearLayout.LayoutParams(dp(28), dp(28)));
        statusView = new TextView(this); statusView.setTextColor(0xFF555555); statusView.setPadding(dp(8), 0, 0, 0); pRow.addView(statusView, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        root.addView(pRow);

        ScrollView scroll = new ScrollView(this);
        results = new LinearLayout(this); results.setOrientation(LinearLayout.VERTICAL); scroll.addView(results);
        root.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        setContentView(root);
    }

    private void showApiKeyDialog(boolean required) {
        EditText input = new EditText(this);
        input.setHint("sk-or-v1-…"); input.setSingleLine(true);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        input.setText(apiKey()); input.setSelection(input.length());
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("OpenRouter API key")
                .setMessage("LLM Council uses OpenRouter. The key is stored only in this app's private preferences on this phone.")
                .setView(input)
                .setPositiveButton("Save", null)
                .setNegativeButton(required ? "Exit" : "Cancel", null)
                .create();
        dialog.setOnShowListener(x -> {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                String key = input.getText().toString().trim();
                if (key.isEmpty()) { Toast.makeText(this, "Enter your OpenRouter API key.", Toast.LENGTH_SHORT).show(); return; }
                prefs.edit().putString("openrouter_api_key", key).apply(); dialog.dismiss();
            });
            if (required) dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener(v -> finish());
        });
        dialog.setCancelable(!required); dialog.show();
    }

    private void showSettings() {
        new AlertDialog.Builder(this).setTitle("Settings")
                .setItems(new String[]{"OpenRouter API key", "About"}, (d, which) -> {
                    if (which == 0) showApiKeyDialog(false);
                    else new AlertDialog.Builder(this).setTitle("About")
                            .setMessage("Personal-use Android port of karpathy/llm-council, pinned to upstream commit 92e1fccb1bdcf1bab7221aa9ed90f9dc72529131. Council stages and model configuration are preserved. Upstream currently has no licence file, so this build is not presented for redistribution.")
                            .setPositiveButton("OK", null).show();
                }).show();
    }

    private void setBusy(boolean busy) {
        askButton.setEnabled(!busy); historyButton.setEnabled(!busy); settingsButton.setEnabled(!busy);
        progress.setVisibility(busy ? View.VISIBLE : View.GONE);
    }

    private void runCouncil() {
        String q = questionInput.getText().toString().trim();
        if (q.isEmpty()) { Toast.makeText(this, "Enter a question first.", Toast.LENGTH_SHORT).show(); return; }
        if (apiKey().isEmpty()) { showApiKeyDialog(true); return; }
        results.removeAllViews(); setBusy(true); statusView.setText("Stage 1/3 · collecting council responses…");

        CompletableFuture.runAsync(() -> {
            try {
                List<ModelResponse> s1 = stage1(q);
                if (s1.isEmpty()) throw new Exception("All models failed to respond. Please try again.");
                runOnUiThread(() -> { renderStage1(s1); statusView.setText("Stage 2/3 · peer ranking…"); });

                Map<String,String> labels = new LinkedHashMap<>();
                List<RankingResponse> s2 = stage2(q, s1, labels);
                List<AggregateRank> agg = aggregate(s2, labels);
                runOnUiThread(() -> { renderStage2(s2, agg); statusView.setText("Stage 3/3 · chairman synthesis…"); });

                ModelResponse s3 = stage3(q, s1, s2);
                String title = conversationTitle(q);
                save(title, q, s1, s2, agg, s3);
                runOnUiThread(() -> { renderStage3(s3); statusView.setText("Council complete"); setBusy(false); });
            } catch (Exception e) {
                runOnUiThread(() -> { card("Error", e.getMessage() == null ? e.toString() : e.getMessage(), 0xFFFFE8E8); statusView.setText("Council run failed"); setBusy(false); });
            }
        }, executor);
    }

    private List<ModelResponse> stage1(String q) {
        Map<String,String> m = parallel(COUNCIL_MODELS, q);
        List<ModelResponse> out = new ArrayList<>();
        for (String model : COUNCIL_MODELS) if (m.get(model) != null) out.add(new ModelResponse(model, m.get(model)));
        return out;
    }

    private List<RankingResponse> stage2(String q, List<ModelResponse> s1, Map<String,String> labels) {
        StringBuilder rs = new StringBuilder();
        for (int i=0;i<s1.size();i++) {
            String label = "Response " + (char)('A'+i); labels.put(label, s1.get(i).model);
            if (i>0) rs.append("\n\n"); rs.append(label).append(":\n").append(s1.get(i).response);
        }
        String p = "You are evaluating different responses to the following question:\n\n"+
                "Question: "+q+"\n\nHere are the responses from different models (anonymized):\n\n"+rs+"\n\n"+
                "Your task:\n1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.\n"+
                "2. Then, at the very end of your response, provide a final ranking.\n\n"+
                "IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:\n"+
                "- Start with the line \"FINAL RANKING:\" (all caps, with colon)\n"+
                "- Then list the responses from best to worst as a numbered list\n"+
                "- Each line should be: number, period, space, then ONLY the response label (e.g., \"1. Response A\")\n"+
                "- Do not add any other text or explanations in the ranking section\n\n"+
                "Example of the correct format for your ENTIRE response:\n\n"+
                "Response A provides good detail on X but misses Y...\nResponse B is accurate but lacks depth on Z...\nResponse C offers the most comprehensive answer...\n\n"+
                "FINAL RANKING:\n1. Response C\n2. Response A\n3. Response B\n\nNow provide your evaluation and ranking:";
        Map<String,String> m = parallel(COUNCIL_MODELS, p);
        List<RankingResponse> out = new ArrayList<>();
        for (String model : COUNCIL_MODELS) if (m.get(model) != null) out.add(new RankingResponse(model, m.get(model), parseRanking(m.get(model))));
        return out;
    }

    private ModelResponse stage3(String q, List<ModelResponse> s1, List<RankingResponse> s2) {
        StringBuilder a = new StringBuilder(), b = new StringBuilder();
        for (int i=0;i<s1.size();i++) { if (i>0) a.append("\n\n"); a.append("Model: ").append(s1.get(i).model).append("\nResponse: ").append(s1.get(i).response); }
        for (int i=0;i<s2.size();i++) { if (i>0) b.append("\n\n"); b.append("Model: ").append(s2.get(i).model).append("\nRanking: ").append(s2.get(i).ranking); }
        String p = "You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.\n\n"+
                "Original Question: "+q+"\n\nSTAGE 1 - Individual Responses:\n"+a+"\n\nSTAGE 2 - Peer Rankings:\n"+b+"\n\n"+
                "Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:\n"+
                "- The individual responses and their insights\n- The peer rankings and what they reveal about response quality\n- Any patterns of agreement or disagreement\n\n"+
                "Provide a clear, well-reasoned final answer that represents the council's collective wisdom:";
        String r = query(CHAIRMAN_MODEL, p, 120000);
        return new ModelResponse(CHAIRMAN_MODEL, r == null ? "Error: Unable to generate final synthesis." : r);
    }

    private String conversationTitle(String q) {
        String p = "Generate a very short title (3-5 words maximum) that summarizes the following question.\nThe title should be concise and descriptive. Do not use quotes or punctuation in the title.\n\nQuestion: "+q+"\n\nTitle:";
        String r = query(TITLE_MODEL, p, 30000);
        if (r == null || r.trim().isEmpty()) return "New Conversation";
        r = r.trim().replaceAll("^[\\\"']+|[\\\"']+$", "");
        return r.length() > 50 ? r.substring(0,47)+"..." : r;
    }

    private Map<String,String> parallel(String[] models, String prompt) {
        Map<String,CompletableFuture<String>> fs = new LinkedHashMap<>();
        for (String model : models) fs.put(model, CompletableFuture.supplyAsync(() -> query(model, prompt, 120000), executor));
        CompletableFuture.allOf(fs.values().toArray(new CompletableFuture[0])).join();
        Map<String,String> out = new LinkedHashMap<>();
        for (String model : models) { try { out.put(model, fs.get(model).getNow(null)); } catch(Exception e) { out.put(model,null); } }
        return out;
    }

    private String query(String model, String prompt, int timeout) {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection)new URL(OPENROUTER_URL).openConnection();
            c.setRequestMethod("POST"); c.setConnectTimeout(Math.min(timeout,30000)); c.setReadTimeout(timeout); c.setDoOutput(true);
            c.setRequestProperty("Authorization", "Bearer "+apiKey()); c.setRequestProperty("Content-Type","application/json");
            JSONObject body = new JSONObject(); body.put("model", model);
            JSONArray ms = new JSONArray(); ms.put(new JSONObject().put("role","user").put("content",prompt)); body.put("messages",ms);
            try (OutputStream os = c.getOutputStream()) { os.write(body.toString().getBytes(StandardCharsets.UTF_8)); }
            int code = c.getResponseCode(); InputStream in = code>=200 && code<300 ? c.getInputStream() : c.getErrorStream(); String text = read(in);
            if (code<200 || code>=300) return null;
            JSONObject msg = new JSONObject(text).getJSONArray("choices").getJSONObject(0).getJSONObject("message");
            return msg.isNull("content") ? "" : msg.optString("content","");
        } catch(Exception e) { return null; }
        finally { if (c != null) c.disconnect(); }
    }

    private String read(InputStream in) throws Exception {
        if (in == null) return ""; StringBuilder s = new StringBuilder();
        try(BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) { String line; while((line=br.readLine())!=null) s.append(line).append('\n'); }
        return s.toString();
    }

    private List<String> parseRanking(String text) {
        String section = text; int i = text.indexOf("FINAL RANKING:"); if (i>=0) section = text.substring(i+14);
        List<String> out = new ArrayList<>(); Matcher m = Pattern.compile("\\d+\\.\\s*(Response [A-Z])").matcher(section);
        while(m.find()) out.add(m.group(1)); if(!out.isEmpty()) return out;
        m = Pattern.compile("Response [A-Z]").matcher(section); while(m.find()) out.add(m.group()); return out;
    }

    private List<AggregateRank> aggregate(List<RankingResponse> s2, Map<String,String> labels) {
        Map<String,List<Integer>> pos = new HashMap<>();
        for (RankingResponse r : s2) for (int i=0;i<r.parsed.size();i++) { String model=labels.get(r.parsed.get(i)); if(model!=null) pos.computeIfAbsent(model,k->new ArrayList<>()).add(i+1); }
        List<AggregateRank> out = new ArrayList<>();
        for (Map.Entry<String,List<Integer>> e : pos.entrySet()) { double sum=0; for(int p:e.getValue()) sum+=p; double avg=Math.round(sum/e.getValue().size()*100.0)/100.0; out.add(new AggregateRank(e.getKey(),avg,e.getValue().size())); }
        out.sort(Comparator.comparingDouble(x->x.average)); return out;
    }

    private void header(String s) { TextView v=new TextView(this); v.setText(s); v.setTextSize(18); v.setTypeface(null,1); v.setTextColor(0xFF111111); v.setPadding(0,dp(14),0,dp(6)); results.addView(v); }
    private void card(String t,String b,int color) { LinearLayout c=new LinearLayout(this); c.setOrientation(LinearLayout.VERTICAL); c.setPadding(dp(12),dp(12),dp(12),dp(12)); c.setBackgroundColor(color); LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT); lp.bottomMargin=dp(8); results.addView(c,lp); TextView a=new TextView(this); a.setText(t); a.setTypeface(null,1); a.setTextColor(0xFF222222); c.addView(a); TextView x=new TextView(this); x.setText(b); x.setTextSize(15); x.setTextColor(0xFF222222); x.setTextIsSelectable(true); x.setPadding(0,dp(5),0,0); c.addView(x); }
    private void renderStage1(List<ModelResponse> s1){ header("Stage 1 · Individual responses"); for(ModelResponse r:s1) card(r.model,r.response,0xFFFFFFFF); }
    private void renderStage2(List<RankingResponse> s2,List<AggregateRank> agg){ header("Stage 2 · Peer rankings"); if(!agg.isEmpty()){ StringBuilder s=new StringBuilder(); for(int i=0;i<agg.size();i++){AggregateRank a=agg.get(i); s.append(i+1).append(". ").append(a.model).append(" · avg rank ").append(String.format(Locale.US,"%.2f",a.average)).append(" · ").append(a.count).append(" rankings\n");} card("Aggregate ranking",s.toString().trim(),0xFFEAF4FF);} for(RankingResponse r:s2) card(r.model,r.ranking,0xFFFFFFFF); }
    private void renderStage3(ModelResponse s3){ header("Stage 3 · Chairman synthesis"); card(s3.model,s3.response,0xFFE9F8EE); }

    private void save(String title,String q,List<ModelResponse>s1,List<RankingResponse>s2,List<AggregateRank>agg,ModelResponse s3){
        try{
            JSONArray h=new JSONArray(prefs.getString("history_json","[]")); JSONObject item=new JSONObject().put("title",title).put("query",q).put("timestamp",System.currentTimeMillis()).put("final",s3.response).put("stage3_model",s3.model);
            JSONArray a1=new JSONArray(); for(ModelResponse r:s1)a1.put(new JSONObject().put("model",r.model).put("response",r.response)); item.put("stage1",a1);
            JSONArray a2=new JSONArray(); for(RankingResponse r:s2)a2.put(new JSONObject().put("model",r.model).put("ranking",r.ranking)); item.put("stage2",a2);
            JSONArray aa=new JSONArray(); for(AggregateRank a:agg)aa.put(new JSONObject().put("model",a.model).put("average_rank",a.average).put("rankings_count",a.count)); item.put("aggregate",aa); h.put(item);
            JSONArray keep=new JSONArray(); int start=Math.max(0,h.length()-50); for(int i=start;i<h.length();i++)keep.put(h.get(i)); prefs.edit().putString("history_json",keep.toString()).apply();
        }catch(Exception ignored){}
    }

    private void showHistory(){
        try{
            JSONArray h=new JSONArray(prefs.getString("history_json","[]")); if(h.length()==0){Toast.makeText(this,"No saved conversations yet.",Toast.LENGTH_SHORT).show();return;}
            List<JSONObject> items=new ArrayList<>(); List<String> labels=new ArrayList<>(); SimpleDateFormat f=new SimpleDateFormat("dd MMM yyyy HH:mm",Locale.getDefault());
            for(int i=h.length()-1;i>=0;i--){JSONObject o=h.getJSONObject(i);items.add(o);labels.add(o.optString("title","Conversation")+"\n"+f.format(new Date(o.optLong("timestamp",0))));}
            new AlertDialog.Builder(this).setTitle("Conversation history").setItems(labels.toArray(new String[0]),(d,w)->load(items.get(w))).setNegativeButton("Close",null).show();
        }catch(Exception e){Toast.makeText(this,"Unable to read history.",Toast.LENGTH_SHORT).show();}
    }

    private void load(JSONObject o){
        results.removeAllViews(); questionInput.setText(o.optString("query","")); header(o.optString("title","Conversation")); card("Question",o.optString("query",""),0xFFFFFFFF);
        JSONArray s1=o.optJSONArray("stage1"); if(s1!=null){header("Stage 1 · Individual responses");for(int i=0;i<s1.length();i++){JSONObject r=s1.optJSONObject(i);if(r!=null)card(r.optString("model"),r.optString("response"),0xFFFFFFFF);}}
        JSONArray s2=o.optJSONArray("stage2"); if(s2!=null){header("Stage 2 · Peer rankings");JSONArray ag=o.optJSONArray("aggregate");if(ag!=null&&ag.length()>0){StringBuilder s=new StringBuilder();for(int i=0;i<ag.length();i++){JSONObject a=ag.optJSONObject(i);if(a!=null)s.append(i+1).append(". ").append(a.optString("model")).append(" · avg rank ").append(a.optDouble("average_rank")).append('\n');}card("Aggregate ranking",s.toString().trim(),0xFFEAF4FF);}for(int i=0;i<s2.length();i++){JSONObject r=s2.optJSONObject(i);if(r!=null)card(r.optString("model"),r.optString("ranking"),0xFFFFFFFF);}}
        header("Stage 3 · Chairman synthesis"); card(o.optString("stage3_model",CHAIRMAN_MODEL),o.optString("final",""),0xFFE9F8EE); statusView.setText("Loaded from history");
    }
}
