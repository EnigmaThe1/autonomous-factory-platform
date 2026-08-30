package com.llmcouncil.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity {
    private static final String CHAT_URL = "https://openrouter.ai/api/v1/chat/completions";
    private static final String MODELS_URL = "https://openrouter.ai/api/v1/models";
    private static final String[] DEFAULT_COUNCIL = {
            "openai/gpt-5.1", "google/gemini-3-pro-preview", "anthropic/claude-sonnet-4.5", "x-ai/grok-4"
    };
    private static final String DEFAULT_CHAIRMAN = "google/gemini-3-pro-preview";
    private static final String TITLE_MODEL = "google/gemini-2.5-flash";

    private final ExecutorService executor = Executors.newFixedThreadPool(8);
    private SharedPreferences prefs;
    private EditText questionInput;
    private Button askButton, historyButton, settingsButton;
    private ProgressBar progress;
    private TextView statusView;
    private LinearLayout results;
    private final Map<String,String> lastErrors = Collections.synchronizedMap(new LinkedHashMap<>());

    static class ModelInfo {
        final String id, name;
        ModelInfo(String id, String name) { this.id=id; this.name=name; }
        String label() { return name.equals(id) ? id : name + "\n" + id; }
    }
    static class ModelResponse {
        final String model, response;
        ModelResponse(String model, String response) { this.model=model; this.response=response; }
    }
    static class RankingResponse {
        final String model, ranking;
        final List<String> parsed;
        RankingResponse(String model, String ranking, List<String> parsed) { this.model=model; this.ranking=ranking; this.parsed=parsed; }
    }
    static class AggregateRank {
        final String model; final double average; final int count;
        AggregateRank(String model,double average,int count){this.model=model;this.average=average;this.count=count;}
    }

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs=getSharedPreferences("llm_council_mobile", Context.MODE_PRIVATE);
        buildUi();
        if(apiKey().isEmpty()) showApiKeyDialog(true);
    }
    @Override protected void onDestroy(){executor.shutdownNow();super.onDestroy();}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private String apiKey(){return prefs.getString("openrouter_api_key","").trim();}

    private String[] councilModels(){
        String raw=prefs.getString("council_models","").trim();
        if(raw.isEmpty()) return DEFAULT_COUNCIL.clone();
        String[] a=raw.split("\\n");
        List<String> out=new ArrayList<>();
        for(String s:a) if(!s.trim().isEmpty()) out.add(s.trim());
        return out.isEmpty()?DEFAULT_COUNCIL.clone():out.toArray(new String[0]);
    }
    private String chairmanModel(){return prefs.getString("chairman_model",DEFAULT_CHAIRMAN).trim();}
    private void saveCouncilModels(List<String> ids){prefs.edit().putString("council_models",String.join("\n",ids)).apply();}
    private void saveChairman(String id){prefs.edit().putString("chairman_model",id).apply();}

    private void buildUi(){
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(16),dp(12),dp(16),dp(12));root.setBackgroundColor(0xFFF7F7F8);
        LinearLayout bar=new LinearLayout(this);bar.setOrientation(LinearLayout.HORIZONTAL);bar.setGravity(Gravity.CENTER_VERTICAL);
        TextView title=new TextView(this);title.setText("LLM Council");title.setTextSize(24);title.setTypeface(null,1);title.setTextColor(0xFF111111);bar.addView(title,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        historyButton=new Button(this);historyButton.setText("History");historyButton.setOnClickListener(v->showHistory());bar.addView(historyButton);
        settingsButton=new Button(this);settingsButton.setText("Settings");settingsButton.setOnClickListener(v->showSettings());bar.addView(settingsButton);root.addView(bar);
        TextView desc=new TextView(this);desc.setText("Stage 1 answers · Stage 2 peer ranking · Stage 3 chairman synthesis");desc.setTextColor(0xFF555555);desc.setPadding(0,dp(5),0,dp(10));root.addView(desc);
        questionInput=new EditText(this);questionInput.setHint("Ask the council anything…");questionInput.setMinLines(3);questionInput.setMaxLines(8);questionInput.setGravity(Gravity.TOP|Gravity.START);questionInput.setBackgroundColor(0xFFFFFFFF);questionInput.setPadding(dp(12),dp(12),dp(12),dp(12));root.addView(questionInput,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        askButton=new Button(this);askButton.setText("Ask LLM Council");askButton.setOnClickListener(v->runCouncil());LinearLayout.LayoutParams al=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);al.topMargin=dp(8);root.addView(askButton,al);
        LinearLayout prow=new LinearLayout(this);prow.setOrientation(LinearLayout.HORIZONTAL);prow.setGravity(Gravity.CENTER_VERTICAL);prow.setPadding(0,dp(8),0,dp(6));progress=new ProgressBar(this);progress.setVisibility(View.GONE);prow.addView(progress,new LinearLayout.LayoutParams(dp(28),dp(28)));statusView=new TextView(this);statusView.setTextColor(0xFF555555);statusView.setPadding(dp(8),0,0,0);prow.addView(statusView,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));root.addView(prow);
        ScrollView scroll=new ScrollView(this);results=new LinearLayout(this);results.setOrientation(LinearLayout.VERTICAL);scroll.addView(results);root.addView(scroll,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,0,1));setContentView(root);
    }

    private void showApiKeyDialog(boolean required){
        EditText input=new EditText(this);input.setHint("sk-or-v1-…");input.setSingleLine(true);input.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);input.setText(apiKey());input.setSelection(input.length());
        AlertDialog d=new AlertDialog.Builder(this).setTitle("OpenRouter API key").setMessage("LLM Council uses OpenRouter. The key is stored only in this app's private preferences on this phone.").setView(input).setPositiveButton("Save",null).setNegativeButton(required?"Exit":"Cancel",null).create();
        d.setOnShowListener(x->{d.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{String k=input.getText().toString().trim();if(k.isEmpty()){Toast.makeText(this,"Enter your OpenRouter API key.",Toast.LENGTH_SHORT).show();return;}prefs.edit().putString("openrouter_api_key",k).apply();d.dismiss();});if(required)d.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener(v->finish());});d.setCancelable(!required);d.show();
    }

    private void showSettings(){
        new AlertDialog.Builder(this).setTitle("Settings").setItems(new String[]{"OpenRouter API key","AI models","About"},(d,w)->{
            if(w==0)showApiKeyDialog(false); else if(w==1)showModelSettings(); else new AlertDialog.Builder(this).setTitle("About").setMessage("Personal-use Android port of karpathy/llm-council, based on upstream commit 92e1fccb1bdcf1bab7221aa9ed90f9dc72529131. Council logic is preserved; model selection is configurable from the live OpenRouter catalogue.").setPositiveButton("OK",null).show();
        }).show();
    }

    private void showModelSettings(){
        String[] current=councilModels();
        String msg="Council members ("+current.length+"):\n"+String.join("\n",current)+"\n\nChairman:\n"+chairmanModel();
        new AlertDialog.Builder(this).setTitle("AI models").setMessage(msg).setItems(new String[]{"Select council models","Select chairman","Reset to upstream defaults"},(d,w)->{
            if(w==0)loadModelsAndChoose(true); else if(w==1)loadModelsAndChoose(false); else {prefs.edit().remove("council_models").remove("chairman_model").apply();Toast.makeText(this,"Upstream model defaults restored.",Toast.LENGTH_SHORT).show();}
        }).setNegativeButton("Close",null).show();
    }

    private void loadModelsAndChoose(boolean multi){
        if(apiKey().isEmpty()){showApiKeyDialog(true);return;}
        ProgressDialog pd=new ProgressDialog(this);pd.setMessage("Loading OpenRouter models…");pd.setCancelable(false);pd.show();
        CompletableFuture.supplyAsync(this::fetchModels,executor).whenComplete((models,err)->runOnUiThread(()->{
            pd.dismiss();
            if(err!=null||models==null||models.isEmpty()){new AlertDialog.Builder(this).setTitle("Could not load models").setMessage(err==null?"OpenRouter returned no models.":err.getMessage()).setPositiveButton("OK",null).show();return;}
            if(multi)chooseCouncilModels(models); else chooseChairman(models);
        }));
    }

    private List<ModelInfo> fetchModels(){
        HttpURLConnection c=null;
        try{
            c=(HttpURLConnection)new URL(MODELS_URL).openConnection();c.setRequestMethod("GET");c.setConnectTimeout(20000);c.setReadTimeout(30000);c.setRequestProperty("Authorization","Bearer "+apiKey());c.setRequestProperty("Accept","application/json");
            int code=c.getResponseCode();String text=read(code>=200&&code<300?c.getInputStream():c.getErrorStream());
            if(code<200||code>=300)throw new RuntimeException("OpenRouter HTTP "+code+": "+extractError(text));
            JSONArray data=new JSONObject(text).optJSONArray("data");List<ModelInfo> out=new ArrayList<>();if(data!=null)for(int i=0;i<data.length();i++){JSONObject o=data.optJSONObject(i);if(o==null)continue;String id=o.optString("id","").trim();if(id.isEmpty())continue;String name=o.optString("name",id).trim();out.add(new ModelInfo(id,name.isEmpty()?id:name));}
            Collections.sort(out,(a,b)->a.label().compareToIgnoreCase(b.label()));return out;
        }catch(Exception e){throw new RuntimeException(e.getMessage()==null?e.toString():e.getMessage());}finally{if(c!=null)c.disconnect();}
    }

    private void chooseCouncilModels(List<ModelInfo> models){
        Set<String> selected=new HashSet<>(Arrays.asList(councilModels()));String[] labels=new String[models.size()];boolean[] checked=new boolean[models.size()];for(int i=0;i<models.size();i++){labels[i]=models.get(i).label();checked[i]=selected.contains(models.get(i).id);}
        AlertDialog d=new AlertDialog.Builder(this).setTitle("Council models").setMultiChoiceItems(labels,checked,(x,which,isChecked)->checked[which]=isChecked).setPositiveButton("Save",null).setNeutralButton("Select none",null).setNegativeButton("Cancel",null).create();
        d.setOnShowListener(x->{d.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{List<String> ids=new ArrayList<>();for(int i=0;i<checked.length;i++)if(checked[i])ids.add(models.get(i).id);if(ids.size()<2){Toast.makeText(this,"Select at least two council models.",Toast.LENGTH_SHORT).show();return;}saveCouncilModels(ids);Toast.makeText(this,ids.size()+" council models saved.",Toast.LENGTH_SHORT).show();d.dismiss();});d.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v->{for(int i=0;i<checked.length;i++){checked[i]=false;d.getListView().setItemChecked(i,false);}});});d.show();
    }

    private void chooseChairman(List<ModelInfo> models){
        String[] labels=new String[models.size()];int current=-1;String cm=chairmanModel();for(int i=0;i<models.size();i++){labels[i]=models.get(i).label();if(models.get(i).id.equals(cm))current=i;}final int[] chosen={current};
        new AlertDialog.Builder(this).setTitle("Chairman model").setSingleChoiceItems(labels,current,(d,w)->chosen[0]=w).setPositiveButton("Save",(d,w)->{if(chosen[0]>=0){saveChairman(models.get(chosen[0]).id);Toast.makeText(this,"Chairman saved.",Toast.LENGTH_SHORT).show();}}).setNegativeButton("Cancel",null).show();
    }

    private void setBusy(boolean busy){askButton.setEnabled(!busy);historyButton.setEnabled(!busy);settingsButton.setEnabled(!busy);progress.setVisibility(busy?View.VISIBLE:View.GONE);}

    private void runCouncil(){
        String q=questionInput.getText().toString().trim();if(q.isEmpty()){Toast.makeText(this,"Enter a question first.",Toast.LENGTH_SHORT).show();return;}if(apiKey().isEmpty()){showApiKeyDialog(true);return;}lastErrors.clear();results.removeAllViews();setBusy(true);statusView.setText("Stage 1/3 · collecting council responses…");
        CompletableFuture.runAsync(()->{
            try{
                List<ModelResponse>s1=stage1(q);if(s1.isEmpty())throw new Exception(buildAllFailedMessage());runOnUiThread(()->{renderStage1(s1);statusView.setText("Stage 2/3 · peer ranking…");});
                Map<String,String> labels=new LinkedHashMap<>();List<RankingResponse>s2=stage2(q,s1,labels);List<AggregateRank>agg=aggregate(s2,labels);runOnUiThread(()->{renderStage2(s2,agg);statusView.setText("Stage 3/3 · chairman synthesis…");});
                ModelResponse s3=stage3(q,s1,s2);String title=conversationTitle(q);save(title,q,s1,s2,agg,s3);runOnUiThread(()->{renderStage3(s3);statusView.setText("Council complete");setBusy(false);});
            }catch(Exception e){runOnUiThread(()->{card("Error",e.getMessage()==null?e.toString():e.getMessage(),0xFFFFE8E8);statusView.setText("Council run failed");setBusy(false);});}
        },executor);
    }

    private String buildAllFailedMessage(){StringBuilder s=new StringBuilder("All selected models failed to respond.");s.append("\n\nSelected models:\n");for(String m:councilModels())s.append("• ").append(m).append("\n");if(!lastErrors.isEmpty()){s.append("\nOpenRouter errors:\n");for(Map.Entry<String,String>e:lastErrors.entrySet())s.append("• ").append(e.getKey()).append(": ").append(e.getValue()).append("\n");}s.append("\nCheck Settings → AI models and choose currently available OpenRouter models.");return s.toString();}

    private List<ModelResponse> stage1(String q){String[] models=councilModels();Map<String,String>m=parallel(models,q);List<ModelResponse>out=new ArrayList<>();for(String model:models)if(m.get(model)!=null)out.add(new ModelResponse(model,m.get(model)));return out;}

    private List<RankingResponse> stage2(String q,List<ModelResponse>s1,Map<String,String>labels){
        StringBuilder rs=new StringBuilder();for(int i=0;i<s1.size();i++){String label="Response "+(char)('A'+i);labels.put(label,s1.get(i).model);if(i>0)rs.append("\n\n");rs.append(label).append(":\n").append(s1.get(i).response);}
        String p="You are evaluating different responses to the following question:\n\nQuestion: "+q+"\n\nHere are the responses from different models (anonymized):\n\n"+rs+"\n\nYour task:\n1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.\n2. Then, at the very end of your response, provide a final ranking.\n\nIMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:\n- Start with the line \"FINAL RANKING:\" (all caps, with colon)\n- Then list the responses from best to worst as a numbered list\n- Each line should be: number, period, space, then ONLY the response label (e.g., \"1. Response A\")\n- Do not add any other text or explanations in the ranking section\n\nExample of the correct format for your ENTIRE response:\n\nResponse A provides good detail on X but misses Y...\nResponse B is accurate but lacks depth on Z...\nResponse C offers the most comprehensive answer...\n\nFINAL RANKING:\n1. Response C\n2. Response A\n3. Response B\n\nNow provide your evaluation and ranking:";
        String[] models=councilModels();Map<String,String>m=parallel(models,p);List<RankingResponse>out=new ArrayList<>();for(String model:models)if(m.get(model)!=null)out.add(new RankingResponse(model,m.get(model),parseRanking(m.get(model))));return out;
    }

    private ModelResponse stage3(String q,List<ModelResponse>s1,List<RankingResponse>s2){StringBuilder a=new StringBuilder(),b=new StringBuilder();for(int i=0;i<s1.size();i++){if(i>0)a.append("\n\n");a.append("Model: ").append(s1.get(i).model).append("\nResponse: ").append(s1.get(i).response);}for(int i=0;i<s2.size();i++){if(i>0)b.append("\n\n");b.append("Model: ").append(s2.get(i).model).append("\nRanking: ").append(s2.get(i).ranking);}String p="You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.\n\nOriginal Question: "+q+"\n\nSTAGE 1 - Individual Responses:\n"+a+"\n\nSTAGE 2 - Peer Rankings:\n"+b+"\n\nYour task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:\n- The individual responses and their insights\n- The peer rankings and what they reveal about response quality\n- Any patterns of agreement or disagreement\n\nProvide a clear, well-reasoned final answer that represents the council's collective wisdom:";String cm=chairmanModel();String r=query(cm,p,120000);return new ModelResponse(cm,r==null?"Error: Unable to generate final synthesis. "+lastErrors.getOrDefault(cm,""):r);}

    private String conversationTitle(String q){String p="Generate a very short title (3-5 words maximum) that summarizes the following question.\nThe title should be concise and descriptive. Do not use quotes or punctuation in the title.\n\nQuestion: "+q+"\n\nTitle:";String r=query(TITLE_MODEL,p,30000);if(r==null||r.trim().isEmpty())return"New Conversation";r=r.trim().replaceAll("^[\\\"']+|[\\\"']+$","");return r.length()>50?r.substring(0,47)+"...":r;}

    private Map<String,String> parallel(String[]models,String prompt){Map<String,CompletableFuture<String>>fs=new LinkedHashMap<>();for(String model:models)fs.put(model,CompletableFuture.supplyAsync(()->query(model,prompt,120000),executor));CompletableFuture.allOf(fs.values().toArray(new CompletableFuture[0])).join();Map<String,String>out=new LinkedHashMap<>();for(String model:models){try{out.put(model,fs.get(model).getNow(null));}catch(Exception e){out.put(model,null);}}return out;}

    private String query(String model,String prompt,int timeout){HttpURLConnection c=null;try{c=(HttpURLConnection)new URL(CHAT_URL).openConnection();c.setRequestMethod("POST");c.setConnectTimeout(Math.min(timeout,30000));c.setReadTimeout(timeout);c.setDoOutput(true);c.setRequestProperty("Authorization","Bearer "+apiKey());c.setRequestProperty("Content-Type","application/json");JSONObject body=new JSONObject();body.put("model",model);JSONArray ms=new JSONArray();ms.put(new JSONObject().put("role","user").put("content",prompt));body.put("messages",ms);try(OutputStream os=c.getOutputStream()){os.write(body.toString().getBytes(StandardCharsets.UTF_8));}int code=c.getResponseCode();String text=read(code>=200&&code<300?c.getInputStream():c.getErrorStream());if(code<200||code>=300){lastErrors.put(model,"HTTP "+code+" — "+extractError(text));return null;}JSONObject msg=new JSONObject(text).getJSONArray("choices").getJSONObject(0).getJSONObject("message");lastErrors.remove(model);return msg.isNull("content")?"":msg.optString("content","");}catch(Exception e){lastErrors.put(model,e.getMessage()==null?e.toString():e.getMessage());return null;}finally{if(c!=null)c.disconnect();}}

    private String extractError(String text){try{JSONObject o=new JSONObject(text);JSONObject e=o.optJSONObject("error");if(e!=null)return e.optString("message",text);return o.optString("message",text);}catch(Exception x){return text==null?"Unknown error":(text.length()>250?text.substring(0,250):text);}}
    private String read(InputStream in)throws Exception{if(in==null)return"";BufferedReader b=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8));StringBuilder s=new StringBuilder();String l;while((l=b.readLine())!=null)s.append(l);return s.toString();}

    private List<String> parseRanking(String text){List<String>out=new ArrayList<>();String src=text;int i=text.indexOf("FINAL RANKING:");if(i>=0)src=text.substring(i+14);Matcher m=Pattern.compile("Response [A-Z]").matcher(src);while(m.find())out.add(m.group());return out;}
    private List<AggregateRank> aggregate(List<RankingResponse>s2,Map<String,String>labels){Map<String,List<Integer>>pos=new HashMap<>();for(RankingResponse r:s2)for(int i=0;i<r.parsed.size();i++){String model=labels.get(r.parsed.get(i));if(model!=null)pos.computeIfAbsent(model,k->new ArrayList<>()).add(i+1);}List<AggregateRank>out=new ArrayList<>();for(Map.Entry<String,List<Integer>>e:pos.entrySet()){double sum=0;for(int x:e.getValue())sum+=x;out.add(new AggregateRank(e.getKey(),Math.round(sum/e.getValue().size()*100.0)/100.0,e.getValue().size()));}Collections.sort(out,Comparator.comparingDouble(a->a.average));return out;}

    private void renderStage1(List<ModelResponse>s){StringBuilder b=new StringBuilder();for(ModelResponse r:s)b.append(r.model).append("\n").append(r.response).append("\n\n");card("Stage 1 · Individual answers",b.toString().trim(),0xFFFFFFFF);}
    private void renderStage2(List<RankingResponse>s,List<AggregateRank>a){StringBuilder b=new StringBuilder();for(RankingResponse r:s)b.append(r.model).append("\n").append(r.ranking).append("\n\n");if(!a.isEmpty()){b.append("Aggregate ranking\n");int n=1;for(AggregateRank x:a)b.append(n++).append(". ").append(x.model).append(" — avg ").append(x.average).append("\n");}card("Stage 2 · Peer ranking",b.toString().trim(),0xFFF2F4FF);}
    private void renderStage3(ModelResponse r){card("Stage 3 · Chairman · "+r.model,r.response,0xFFEAF8EE);}
    private void card(String title,String body,int color){LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(12),dp(10),dp(12),dp(10));box.setBackgroundColor(color);TextView h=new TextView(this);h.setText(title);h.setTextSize(17);h.setTypeface(null,1);h.setTextColor(0xFF222222);box.addView(h);TextView t=new TextView(this);t.setText(body);t.setTextSize(15);t.setTextColor(0xFF222222);t.setTextIsSelectable(true);t.setPadding(0,dp(6),0,0);box.addView(t);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);lp.bottomMargin=dp(10);results.addView(box,lp);}

    private void save(String title,String q,List<ModelResponse>s1,List<RankingResponse>s2,List<AggregateRank>agg,ModelResponse s3){try{JSONArray h=new JSONArray(prefs.getString("history_json","[]"));JSONObject item=new JSONObject();item.put("title",title);item.put("query",q);item.put("timestamp",System.currentTimeMillis());item.put("final_model",s3.model);item.put("final",s3.response);h.put(item);JSONArray keep=new JSONArray();int start=Math.max(0,h.length()-50);for(int i=start;i<h.length();i++)keep.put(h.get(i));prefs.edit().putString("history_json",keep.toString()).apply();}catch(Exception ignored){}}
    private void showHistory(){try{JSONArray h=new JSONArray(prefs.getString("history_json","[]"));if(h.length()==0){Toast.makeText(this,"No saved conversations yet.",Toast.LENGTH_SHORT).show();return;}List<JSONObject>items=new ArrayList<>();List<String>labels=new ArrayList<>();SimpleDateFormat f=new SimpleDateFormat("dd MMM yyyy HH:mm",Locale.getDefault());for(int i=h.length()-1;i>=0;i--){JSONObject o=h.getJSONObject(i);items.add(o);labels.add(o.optString("title","Conversation")+"\n"+f.format(new Date(o.optLong("timestamp",0))));}new AlertDialog.Builder(this).setTitle("History").setItems(labels.toArray(new String[0]),(d,w)->{JSONObject o=items.get(w);new AlertDialog.Builder(this).setTitle(o.optString("title","Conversation")).setMessage("Question:\n"+o.optString("query","")+"\n\nChairman ("+o.optString("final_model","")+"):\n"+o.optString("final","")).setPositiveButton("Close",null).show();}).setNegativeButton("Close",null).show();}catch(Exception e){Toast.makeText(this,"Could not read history.",Toast.LENGTH_SHORT).show();}}
}
